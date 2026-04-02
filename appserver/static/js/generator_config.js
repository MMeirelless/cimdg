/**
 * CIM Data Generator — Generator Configuration dashboard logic.
 *
 * Handles the "Generate & Index" button by posting to the REST handler,
 * which runs the search job server-side (avoiding SPL safeguard restrictions
 * on | collect in dashboard context).
 */

require([
    "jquery",
    "splunkjs/mvc",
    "splunkjs/mvc/simplexml/ready!"
], function($, mvc) {

    var tokens = mvc.Components.get("default");

    // -----------------------------------------------------------------------
    // Generate & Index button
    // -----------------------------------------------------------------------

    var $btn        = $("#btn_generate_index");
    var $statusWrap = $("#generate_status_wrap");

    function setStatus(message, type, details) {
        var colors = {
            info:    { bg: "#5cb8b2", border: "#4a9e98" },
            success: { bg: "#53a051", border: "#458945" },
            error:   { bg: "#dc4e41", border: "#c43a2f" },
            warning: { bg: "#f8be34", border: "#e0a820" }
        };
        var c = colors[type] || colors.info;

        var html = '<span style="font-weight:600;">' + escapeHtml(message) + '</span>';

        if (details) {
            html += ' <a href="#" class="toggle-details" '
                  + 'style="color:#fff;text-decoration:underline;margin-left:8px;font-size:12px;">'
                  + 'Show details</a>'
                  + '<pre class="error-details" style="display:none;margin-top:8px;'
                  + 'padding:10px;background:rgba(0,0,0,0.2);border-radius:4px;'
                  + 'font-size:11px;white-space:pre-wrap;word-break:break-all;'
                  + 'max-height:200px;overflow-y:auto;color:#fff;">'
                  + escapeHtml(details) + '</pre>';
        }

        $statusWrap
            .html(html)
            .css({
                "background": c.bg,
                "border-left": "4px solid " + c.border,
                "color": "#fff",
                "padding": "10px 15px",
                "border-radius": "4px",
                "margin-top": "10px",
                "display": "block"
            });

        // Toggle details
        $statusWrap.find(".toggle-details").off("click").on("click", function(e) {
            e.preventDefault();
            var $details = $statusWrap.find(".error-details");
            var $link = $(this);
            if ($details.is(":visible")) {
                $details.slideUp(150);
                $link.text("Show details");
            } else {
                $details.slideDown(150);
                $link.text("Hide details");
            }
        });
    }

    function escapeHtml(str) {
        if (!str) return "";
        return str.replace(/&/g, "&amp;")
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;")
                  .replace(/"/g, "&quot;");
    }

    $btn.on("click", function(e) {
        e.preventDefault();

        var model     = tokens.get("selected_model");
        var count     = parseInt(tokens.get("event_count"), 10) || 100;
        var timerange = tokens.get("timerange") || "-1h";
        var index     = tokens.get("target_index") || "synthetic_cim";

        if (!model) {
            setStatus("Please select a CIM Data Model first.", "warning");
            return;
        }

        if (count < 1 || count > 100000) {
            setStatus("Event count must be between 1 and 100,000.", "warning");
            return;
        }

        $btn.prop("disabled", true).text("Generating...");
        setStatus(
            "Generating " + count + " " + model + " events into " + index + "...",
            "info"
        );

        $.ajax({
            url: Splunk.util.make_url(
                "/splunkd/__raw/services/cimdg/generate"
            ),
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                model: model,
                count: count,
                index: index,
                timerange: timerange
            }),
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data;
                try {
                    data = (typeof response === "string")
                        ? JSON.parse(response)
                        : response;
                } catch (parseErr) {
                    setStatus(
                        "Unexpected response from server.",
                        "warning",
                        "Raw response:\n" + String(response)
                    );
                    $btn.prop("disabled", false).text("Generate & Index");
                    return;
                }

                if (data.success) {
                    setStatus(
                        data.message || "Events generated successfully!",
                        "success"
                    );
                } else if (data.error) {
                    setStatus("Generation failed.", "error", data.error);
                } else {
                    setStatus(
                        "Generation completed with warnings.",
                        "warning",
                        JSON.stringify(data, null, 2)
                    );
                }
                $btn.prop("disabled", false).text("Generate & Index");
            },
            error: function(xhr) {
                var msg = "Generation failed.";
                var details = "HTTP " + xhr.status + " " + xhr.statusText;

                try {
                    var body = xhr.responseText || "";
                    var err = JSON.parse(body);
                    if (err.error) {
                        msg = err.error;
                    }
                    details += "\n\nServer response:\n"
                             + JSON.stringify(err, null, 2);
                } catch (parseErr) {
                    details += "\n\nRaw response:\n"
                             + (xhr.responseText || "(empty)");
                }

                details += "\n\nRequest:\n"
                         + "POST /services/cimdg/generate\n"
                         + JSON.stringify({
                               model: model,
                               count: count,
                               index: index,
                               timerange: timerange
                           }, null, 2);

                setStatus(msg, "error", details);
                $btn.prop("disabled", false).text("Generate & Index");
            }
        });
    });
});
