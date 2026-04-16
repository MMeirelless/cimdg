/**
 * CIM Data Generator  -  Generator Configuration dashboard logic.
 *
 * - "Generate & Index" button → REST handler (server-side | collect)
 * - "Purge Generated Data" → modal with data summary → REST handler (server-side | delete)
 * - Active generator warning banner
 * - License impact estimator
 *
 * All event handlers use delegation ($(document).on) so they survive
 * SimpleXML re-rendering HTML panels on token changes.
 */

require([
    "jquery",
    "splunkjs/mvc",
    "splunkjs/mvc/searchmanager",
    "splunkjs/mvc/simplexml/ready!"
], function($, mvc, SearchManager) {

    var tokens = mvc.Components.get("default");

    // -----------------------------------------------------------------------
    // Utilities
    // -----------------------------------------------------------------------

    function escapeHtml(val) {
        if (val === null || val === undefined) return "";
        var str = String(val);
        return str.replace(/&/g, "&amp;")
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;")
                  .replace(/"/g, "&quot;");
    }

    function setStatus(message, type, details) {
        var $statusWrap = $("#generate_status_wrap");
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
    }

    // Toggle error details (delegated)
    $(document).on("click", ".toggle-details", function(e) {
        e.preventDefault();
        var $details = $(this).siblings(".error-details");
        if ($details.is(":visible")) {
            $details.slideUp(150);
            $(this).text("Show details");
        } else {
            $details.slideDown(150);
            $(this).text("Hide details");
        }
    });

    // -----------------------------------------------------------------------
    // Active generator warning banner
    // -----------------------------------------------------------------------

    function checkActiveGenerators() {
        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/cimdg/status"),
            type: "GET",
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data = (typeof response === "string") ? JSON.parse(response) : response;
                if (data.active_count && data.active_count > 0) {
                    $("#active_generator_warning").show();
                } else {
                    $("#active_generator_warning").hide();
                }
            }
        });
    }
    checkActiveGenerators();
    setInterval(checkActiveGenerators, 30000);

    // -----------------------------------------------------------------------
    // Continuous generators table with toggle
    // -----------------------------------------------------------------------

    var _allInputs = [];
    var _genPage = 1;
    var _genPerPage = 10;

    function loadGeneratorsTable() {
        var $wrap = $("#generators_table_wrap");

        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/cimdg/status"),
            type: "GET",
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data = (typeof response === "string") ? JSON.parse(response) : response;
                _allInputs = data.inputs || [];
                _genPage = 1;
                renderGeneratorsTable();
            },
            error: function() {
                $wrap.html('<p style="color:#dc4e41;">Failed to load generator status.</p>');
            }
        });
    }

    function getFilteredInputs() {
        var fName = ($("#gen_filter_name").val() || "").toLowerCase();
        var fModel = ($("#gen_filter_model").val() || "").toLowerCase();
        var fCat = $("#gen_filter_category").val() || "";
        var fStatus = $("#gen_filter_status").val() || "";

        return _allInputs.filter(function(inp) {
            if (fName && inp.name.toLowerCase().indexOf(fName) === -1) return false;
            if (fModel && (inp.model || "").toLowerCase().indexOf(fModel) === -1) return false;
            if (fCat && (inp.category || "") !== fCat) return false;
            if (fStatus === "active" && !(inp.disabled === "0" || inp.disabled === false)) return false;
            if (fStatus === "disabled" && (inp.disabled === "0" || inp.disabled === false)) return false;
            return true;
        });
    }

    function renderGeneratorsTable() {
        var $wrap = $("#generators_table_wrap");
        var filtered = getFilteredInputs();
        var totalPages = Math.max(1, Math.ceil(filtered.length / _genPerPage));
        if (_genPage > totalPages) _genPage = totalPages;
        var start = (_genPage - 1) * _genPerPage;
        var pageItems = filtered.slice(start, start + _genPerPage);

        var fSt = 'padding:4px 8px; font-size:12px; border:1px solid #ccc; border-radius:3px;';
        var html = '<div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:10px; align-items:center;">'
            + '<input id="gen_filter_name" type="text" placeholder="Filter by name..." style="' + fSt + ' width:140px;" value="' + escapeHtml($("#gen_filter_name").val() || "") + '"/>'
            + '<input id="gen_filter_model" type="text" placeholder="Filter by model..." style="' + fSt + ' width:140px;" value="' + escapeHtml($("#gen_filter_model").val() || "") + '"/>'
            + '<select id="gen_filter_category" style="' + fSt + '">'
            + '<option value="">All Categories</option>'
            + '<option value="Security"' + ($("#gen_filter_category").val() === "Security" ? " selected" : "") + '>Security</option>'
            + '<option value="Infrastructure"' + ($("#gen_filter_category").val() === "Infrastructure" ? " selected" : "") + '>Infrastructure</option>'
            + '<option value="Operations"' + ($("#gen_filter_category").val() === "Operations" ? " selected" : "") + '>Operations</option>'
            + '</select>'
            + '<select id="gen_filter_status" style="' + fSt + '">'
            + '<option value="">All Status</option>'
            + '<option value="active"' + ($("#gen_filter_status").val() === "active" ? " selected" : "") + '>Active</option>'
            + '<option value="disabled"' + ($("#gen_filter_status").val() === "disabled" ? " selected" : "") + '>Disabled</option>'
            + '</select>'
            + '<span style="font-size:12px; color:#666; margin-left:auto;">'
            + 'Showing ' + (filtered.length ? start + 1 : 0) + '–' + Math.min(start + _genPerPage, filtered.length)
            + ' of ' + filtered.length + '</span>'
            + '</div>';

        if (pageItems.length === 0) {
            html += '<p style="color:#999; font-style:italic; padding:10px 0;">No generators match the current filters.</p>';
        } else {
            var cellSt = 'padding:6px 8px;';
            var inputSt = 'width:58px; padding:2px 6px; font-size:12px; border:1px solid #ccc; border-radius:3px; text-align:right;';
            var idxInputSt = 'width:110px; padding:2px 6px; font-size:12px; border:1px solid #ccc; border-radius:3px;';
            var btnSt = 'padding:3px 10px; font-size:11px; border:none; border-radius:3px; color:#fff; cursor:pointer;';

            html += '<table style="width:100%; border-collapse:collapse; font-size:13px;">'
                + '<thead><tr style="background:#f4f5f7; border-bottom:2px solid #ddd;">'
                + '<th style="' + cellSt + ' text-align:left;">Model</th>'
                + '<th style="' + cellSt + ' text-align:left;">Category</th>'
                + '<th style="' + cellSt + ' text-align:right;">EPI</th>'
                + '<th style="' + cellSt + ' text-align:right;">Interval</th>'
                + '<th style="' + cellSt + ' text-align:left;">Index</th>'
                + '<th style="' + cellSt + ' text-align:center;">Actions</th>'
                + '</tr></thead><tbody>';

            pageItems.forEach(function(inp) {
                var isActive = inp.disabled === "0" || inp.disabled === false;
                var badge = isActive
                    ? '<span style="background:#53a051;color:#fff;padding:2px 6px;border-radius:3px;font-size:10px;">Active</span>'
                    : '<span style="background:#999;color:#fff;padding:2px 6px;border-radius:3px;font-size:10px;">Off</span>';
                var toggleAction = isActive ? "disable" : "enable";
                var toggleColor = isActive ? "#dc4e41" : "#53a051";
                var toggleLabel = isActive ? "Disable" : "Enable";
                var sn = escapeHtml(inp.name);

                html += '<tr style="border-bottom:1px solid #eee;" data-input="' + sn + '">'
                    + '<td style="' + cellSt + '">' + badge + ' ' + escapeHtml(inp.model) + '</td>'
                    + '<td style="' + cellSt + ' font-size:11px; color:#666;">' + escapeHtml(inp.category || "Other") + '</td>'
                    + '<td style="' + cellSt + ' text-align:right;">'
                    + '<input type="number" class="inp-epi" data-name="' + sn + '" value="' + escapeHtml(inp.events_per_interval) + '" min="1" max="1000" style="' + inputSt + '"/></td>'
                    + '<td style="' + cellSt + ' text-align:right;">'
                    + '<input type="number" class="inp-interval" data-name="' + sn + '" value="' + escapeHtml(inp.interval) + '" min="10" max="3600" style="' + inputSt + '"/></td>'
                    + '<td style="' + cellSt + '">'
                    + '<input type="text" class="inp-index" data-name="' + sn + '" value="' + escapeHtml(inp.index || "synthetic_cim") + '" style="' + idxInputSt + '"/></td>'
                    + '<td style="' + cellSt + ' text-align:center; white-space:nowrap;">'
                    + '<button class="btn-toggle-generator" data-name="' + sn + '" data-action="' + toggleAction + '" '
                    + 'style="' + btnSt + ' background:' + toggleColor + '; margin-right:3px;">' + toggleLabel + '</button>'
                    + '<button class="btn-update-generator" data-name="' + sn + '" '
                    + 'style="' + btnSt + ' background:#5cb8b2;">Save</button>'
                    + '</td></tr>';
            });

            html += '</tbody></table>';
        }

        // Pagination
        if (totalPages > 1) {
            html += '<div style="display:flex; justify-content:center; gap:4px; margin-top:10px;">';
            for (var p = 1; p <= totalPages; p++) {
                var active = p === _genPage;
                html += '<button class="btn-gen-page" data-page="' + p + '" style="'
                    + 'padding:4px 10px; font-size:12px; border:1px solid ' + (active ? '#2ca19b' : '#ccc') + '; '
                    + 'border-radius:3px; cursor:pointer; '
                    + 'background:' + (active ? '#2ca19b' : '#fff') + '; '
                    + 'color:' + (active ? '#fff' : '#333') + ';">' + p + '</button>';
            }
            html += '</div>';
        }

        $wrap.html(html);
    }

    loadGeneratorsTable();

    // Filter handlers: text inputs debounce 2s or Enter key; dropdowns instant
    var _filterTimer = null;
    $(document).on("input", "#gen_filter_name, #gen_filter_model", function() {
        clearTimeout(_filterTimer);
        _filterTimer = setTimeout(function() {
            _genPage = 1;
            renderGeneratorsTable();
        }, 2000);
    });
    $(document).on("keydown", "#gen_filter_name, #gen_filter_model", function(e) {
        if (e.which === 13) {
            clearTimeout(_filterTimer);
            _genPage = 1;
            renderGeneratorsTable();
        }
    });
    $(document).on("change", "#gen_filter_category, #gen_filter_status", function() {
        _genPage = 1;
        renderGeneratorsTable();
    });
    $(document).on("click", ".btn-gen-page", function(e) {
        e.preventDefault();
        _genPage = parseInt($(this).data("page"), 10);
        renderGeneratorsTable();
    });

    // Toggle generator enable/disable (delegated)
    $(document).on("click", ".btn-toggle-generator", function(e) {
        e.preventDefault();
        var $btn = $(this);
        var inputName = $btn.data("name");
        var action = $btn.data("action");

        $btn.prop("disabled", true).text("...");

        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/cimdg/status"),
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ action: action, input_name: inputName }),
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data;
                try { data = (typeof response === "string") ? JSON.parse(response) : response; } catch(pe) { data = {}; }

                if (data.success) {
                    setStatus(data.message || ("Input " + action + "d."), "success");
                } else if (data.error) {
                    setStatus("Toggle failed: " + data.error, "error",
                        data.detail ? "Endpoint: " + (data.endpoint || "") + "\nDetail: " + data.detail : null);
                }
                loadGeneratorsTable();
                checkActiveGenerators();
            },
            error: function(xhr) {
                var msg = "Failed to " + action + " input '" + inputName + "'.";
                var details = "HTTP " + xhr.status;
                try {
                    var err = JSON.parse(xhr.responseText);
                    msg = err.error || msg;
                    details += "\nEndpoint: " + (err.endpoint || "unknown");
                    if (err.detail) details += "\nDetail: " + err.detail;
                } catch(pe) {
                    details += "\n" + (xhr.responseText || "(empty)");
                }
                setStatus(msg, "error", details);
                loadGeneratorsTable();
            }
        });
    });

    // Save updated interval/events_per_interval/index (delegated)
    $(document).on("click", ".btn-update-generator", function(e) {
        e.preventDefault();
        var $btn = $(this);
        var inputName = $btn.data("name");
        var $row = $btn.closest("tr");
        var epi = $row.find(".inp-epi").val();
        var interval = $row.find(".inp-interval").val();
        var idx = $row.find(".inp-index").val();

        $btn.prop("disabled", true).text("...");

        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/cimdg/status"),
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                action: "update",
                input_name: inputName,
                events_per_interval: parseInt(epi, 10) || 10,
                interval: parseInt(interval, 10) || 60,
                index: idx || "synthetic_cim"
            }),
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data;
                try { data = (typeof response === "string") ? JSON.parse(response) : response; } catch(pe) { data = {}; }
                if (data.success) {
                    setStatus(data.message, "success");
                } else {
                    setStatus(data.error || "Update failed.", "error", data.detail || null);
                }
                loadGeneratorsTable();
            },
            error: function(xhr) {
                var msg = "Failed to update input.";
                var details = "HTTP " + xhr.status;
                try {
                    var err = JSON.parse(xhr.responseText);
                    msg = err.error || msg;
                    if (err.detail) details += "\n" + err.detail;
                } catch(pe) { details += "\n" + (xhr.responseText || ""); }
                setStatus(msg, "error", details);
                loadGeneratorsTable();
            }
        });
    });

    // -----------------------------------------------------------------------
    // Attack playbook runner
    // -----------------------------------------------------------------------

    function setPlaybookStatus(message, type) {
        var $wrap = $("#playbook_status_wrap");
        var colors = {
            info: "#5cb8b2", success: "#53a051", error: "#dc4e41", warning: "#f8be34"
        };
        $wrap.html('<span style="font-weight:600;">' + escapeHtml(message) + '</span>')
            .css({
                "background": colors[type] || colors.info,
                "color": "#fff",
                "padding": "10px 15px",
                "border-radius": "4px",
                "display": "block"
            });
    }

    $(document).on("click", "#btn_run_playbook", function(e) {
        e.preventDefault();
        var $btn = $(this);
        var playbook = $("#playbook_select").val();
        var index = tokens.get("target_index") || "synthetic_cim";

        if (!playbook) {
            setPlaybookStatus("Please select a playbook first.", "warning");
            return;
        }

        $btn.prop("disabled", true).text("Running...");
        setPlaybookStatus("Running " + playbook + " playbook...", "info");

        // Call the generate REST handler which writes events directly
        // with correct per-event sourcetypes (no | collect needed)
        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/cimdg/generate"),
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                playbook: playbook,
                index: index
            }),
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data = (typeof response === "string") ? JSON.parse(response) : response;
                if (data.success) {
                    setPlaybookStatus(data.message, "success");
                } else {
                    setPlaybookStatus(data.error || "Playbook completed with warnings.", "warning");
                }
                $btn.prop("disabled", false).text("Run Playbook");
            },
            error: function(xhr) {
                var msg = "Playbook failed.";
                try { msg = JSON.parse(xhr.responseText).error || msg; } catch(pe) {}
                setPlaybookStatus(msg, "error");
                $btn.prop("disabled", false).text("Run Playbook");
            }
        });
    });

    // -----------------------------------------------------------------------
    // License impact estimator
    // -----------------------------------------------------------------------

    function updateLicenseEstimate() {
        var count = parseInt(tokens.get("event_count"), 10) || 100;
        var avgBytes = 500;
        var mbPerBatch = (count * avgBytes) / (1024 * 1024);
        var batchesPerDay = 86400 / 60;
        var mbPerDay = Math.round(mbPerBatch * batchesPerDay * 10) / 10;
        $("#license_estimate").text(mbPerDay + " MB/day");
    }
    tokens.on("change:event_count", updateLicenseEstimate);
    updateLicenseEstimate();

    // -----------------------------------------------------------------------
    // Generate & Index button (delegated)
    // -----------------------------------------------------------------------

    $(document).on("click", "#btn_generate_index", function(e) {
        e.preventDefault();

        var $btn      = $(this);
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

        if (count > 10000) {
            if (!confirm("You are about to generate " + count.toLocaleString() +
                         " events (~" + Math.round(count * 500 / 1024 / 1024 * 10) / 10 +
                         " MB of license). Continue?")) {
                return;
            }
        }

        $btn.prop("disabled", true).text("Generating...");
        setStatus("Generating " + count + " " + model + " events into " + index + "...", "info");

        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/cimdg/generate"),
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ model: model, count: count, index: index, timerange: timerange }),
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data;
                try {
                    data = (typeof response === "string") ? JSON.parse(response) : response;
                } catch (parseErr) {
                    setStatus("Unexpected response.", "warning", "Raw: " + String(response));
                    $btn.prop("disabled", false).text("Generate & Index");
                    return;
                }
                if (data.success) {
                    setStatus(data.message || "Events generated successfully!", "success");
                } else if (data.error) {
                    setStatus("Generation failed.", "error", data.error);
                } else {
                    setStatus("Completed with warnings.", "warning", JSON.stringify(data, null, 2));
                }
                $btn.prop("disabled", false).text("Generate & Index");
            },
            error: function(xhr) {
                var msg = "Generation failed.";
                var details = "HTTP " + xhr.status + " " + xhr.statusText;
                try {
                    var err = JSON.parse(xhr.responseText);
                    if (err.error) msg = err.error;
                    details += "\n\n" + JSON.stringify(err, null, 2);
                } catch (pe) {
                    details += "\n\n" + (xhr.responseText || "(empty)");
                }
                setStatus(msg, "error", details);
                $btn.prop("disabled", false).text("Generate & Index");
            }
        });
    });

    // -----------------------------------------------------------------------
    // Purge modal
    // -----------------------------------------------------------------------

    // Inject modal HTML into the page (once)
    $("body").append(
        '<div id="purge_modal_overlay" style="display:none; position:fixed; top:0; left:0; '
      + 'width:100%; height:100%; background:rgba(0,0,0,0.55); z-index:10000;">'
      + '<div id="purge_modal" style="position:absolute; top:50%; left:50%; '
      + 'transform:translate(-50%,-50%); background:#fff; border-radius:8px; '
      + 'width:90%; max-width:680px; max-height:80vh; overflow-y:auto; '
      + 'box-shadow:0 8px 32px rgba(0,0,0,0.3); box-sizing:border-box;">'

      // Header
      + '<div style="padding:16px 24px; border-bottom:1px solid #ddd; display:flex; '
      + 'align-items:center; gap:10px;">'
      + '<span style="font-size:20px;">&#9888;</span>'
      + '<span style="font-size:16px; font-weight:700; color:#dc4e41;">Purge Generated Data</span>'
      + '</div>'

      // Body
      + '<div style="padding:20px 24px;">'
      + '<div style="background:#fff3cd; border:1px solid #f0c36d; border-radius:4px; '
      + 'padding:12px 16px; margin-bottom:16px; font-size:13px; color:#856404;">'
      + '<b>Caution:</b> This action will permanently delete CIMDG-generated events '
      + '(<code>sourcetype=cimdg:synthetic:*</code>) from the target index '
      + 'using the <code>| delete</code> command. This cannot be undone. '
      + 'Your Splunk user must have the <b>can_delete</b> role to perform this action. '
      + 'Deleted data still counts against today\'s license usage.'
      + '</div>'
      + '<p style="font-size:13px; margin-bottom:12px;">The following CIMDG-generated data '
      + '(<code>sourcetype=cimdg:synthetic:*</code>) will be deleted from '
      + 'index <b id="purge_modal_index"></b>:</p>'
      + '<div id="purge_modal_loading" style="text-align:center; padding:20px; color:#999;">'
      + 'Loading data summary...</div>'
      + '<table id="purge_modal_table" style="display:none; width:100%; border-collapse:collapse; '
      + 'table-layout:fixed; font-size:13px; margin-bottom:16px;">'
      + '<thead><tr style="background:#f4f5f7; border-bottom:2px solid #ddd;">'
      + '<th style="padding:8px 10px; text-align:left; width:30%;">Sourcetype</th>'
      + '<th style="padding:8px 10px; text-align:left; width:30%;">Source</th>'
      + '<th style="padding:8px 10px; text-align:left; width:22%;">Host</th>'
      + '<th style="padding:8px 10px; text-align:right; width:18%;">Events</th>'
      + '</tr></thead>'
      + '<tbody id="purge_modal_tbody"></tbody>'
      + '<tfoot><tr style="border-top:2px solid #ddd; font-weight:700;">'
      + '<td style="padding:8px 12px;" colspan="3">Total</td>'
      + '<td id="purge_modal_total" style="padding:8px 12px; text-align:right;"></td>'
      + '</tr></tfoot>'
      + '</table>'
      + '<div id="purge_modal_empty" style="display:none; text-align:center; '
      + 'padding:16px; color:#999; font-style:italic;">No data found in this index.</div>'
      + '<div id="purge_modal_denied" style="display:none;">'
      + '<div style="background:#f8d7da; border:1px solid #f5c6cb; border-radius:4px; '
      + 'padding:16px 20px; color:#721c24; font-size:13px;">'
      + '<b>Access Denied:</b> Your Splunk user does not have the <b>can_delete</b> role, '
      + 'which is required to delete indexed data. '
      + 'Please contact your Splunk administrator to request the <b>can_delete</b> role '
      + 'or ask them to purge the data on your behalf.'
      + '</div>'
      + '</div>'
      + '</div>'

      // Footer
      + '<div style="padding:12px 24px; border-top:1px solid #ddd; display:flex; '
      + 'justify-content:flex-end; gap:10px;">'
      + '<button id="purge_modal_cancel" class="btn" style="padding:8px 20px;">Cancel</button>'
      + '<button id="purge_modal_confirm" class="btn" style="padding:8px 20px; '
      + 'background:#dc4e41; color:#fff; border:none; border-radius:4px; font-weight:600;" '
      + 'disabled="disabled">Confirm Purge</button>'
      + '</div>'

      + '</div></div>'
    );

    function openPurgeModal(index) {
        var $overlay = $("#purge_modal_overlay");
        var $table   = $("#purge_modal_table");
        var $tbody   = $("#purge_modal_tbody");
        var $loading = $("#purge_modal_loading");
        var $empty   = $("#purge_modal_empty");
        var $denied  = $("#purge_modal_denied");
        var $confirm = $("#purge_modal_confirm");
        var $warning = $overlay.find("[style*='fff3cd']"); // caution banner

        // Reset state
        $("#purge_modal_index").text(index);
        $tbody.empty();
        $table.hide();
        $empty.hide();
        $denied.hide();
        $warning.show();
        $loading.show().text("Checking permissions...");
        $confirm.prop("disabled", true).text("Confirm Purge").show();
        $overlay.fadeIn(150);

        // Step 1: Check if user has can_delete role
        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/authentication/current-context"),
            type: "GET",
            data: { output_mode: "json" },
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data = (typeof response === "string") ? JSON.parse(response) : response;
                var roles = [];
                try {
                    roles = data.entry[0].content.roles || [];
                } catch (e) { /* fallback: empty roles */ }

                var hasDeleteRole = roles.indexOf("can_delete") !== -1;

                if (!hasDeleteRole) {
                    // User lacks can_delete role  -  show denial, hide action controls
                    $loading.hide();
                    $warning.hide();
                    $denied.show();
                    $confirm.hide();
                    return;
                }

                // Step 2: User has permission  -  fetch data summary
                $loading.text("Loading data summary...");
                fetchPurgeSummary(index);
            },
            error: function() {
                $loading.hide();
                $warning.hide();
                $denied.show();
                $confirm.hide();
            }
        });
    }

    function fetchPurgeSummary(index) {
        var $table   = $("#purge_modal_table");
        var $tbody   = $("#purge_modal_tbody");
        var $loading = $("#purge_modal_loading");
        var $empty   = $("#purge_modal_empty");
        var $confirm = $("#purge_modal_confirm");

        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/search/jobs"),
            type: "POST",
            data: {
                search: 'search index=' + index + ' sourcetype=cimdg:synthetic:* | stats count by sourcetype, source, host | sort -count',
                exec_mode: "oneshot",
                output_mode: "json",
                count: 100
            },
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data = (typeof response === "string") ? JSON.parse(response) : response;
                var results = data.results || [];

                $loading.hide();

                if (results.length === 0) {
                    $empty.show();
                    $confirm.prop("disabled", true);
                    return;
                }

                var totalEvents = 0;
                results.forEach(function(row) {
                    var cnt = parseInt(row.count, 10) || 0;
                    totalEvents += cnt;
                    var cellStyle = 'padding:6px 10px; word-break:break-all; overflow-wrap:break-word;';
                    $tbody.append(
                        '<tr style="border-bottom:1px solid #eee;">'
                      + '<td style="' + cellStyle + '">' + escapeHtml(row.sourcetype) + '</td>'
                      + '<td style="' + cellStyle + '">' + escapeHtml(row.source) + '</td>'
                      + '<td style="' + cellStyle + '">' + escapeHtml(row.host) + '</td>'
                      + '<td style="' + cellStyle + ' text-align:right;">' + cnt.toLocaleString() + '</td>'
                      + '</tr>'
                    );
                });

                $("#purge_modal_total").text(totalEvents.toLocaleString());
                $table.show();
                $confirm.prop("disabled", false);
            },
            error: function() {
                $loading.text("Failed to load data summary. You may not have search permissions on this index.");
                $confirm.prop("disabled", true);
            }
        });
    }

    function closePurgeModal() {
        $("#purge_modal_overlay").fadeOut(150);
    }

    function executePurge(index) {
        var $confirm = $("#purge_modal_confirm");
        $confirm.prop("disabled", true).text("Purging...");

        $.ajax({
            url: Splunk.util.make_url("/splunkd/__raw/services/cimdg/purge"),
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ confirm: true, index: index }),
            headers: {
                "X-Splunk-Form-Key": Splunk.util.getFormKey(),
                "X-Requested-With": "XMLHttpRequest"
            },
            success: function(response) {
                var data = (typeof response === "string") ? JSON.parse(response) : response;
                closePurgeModal();
                if (data.success) {
                    setStatus(data.message || "Purge dispatched.", "success");
                } else {
                    setStatus("Purge failed.", "error", data.error);
                }
                $confirm.prop("disabled", false).text("Confirm Purge");
            },
            error: function(xhr) {
                closePurgeModal();
                var msg = "Purge failed.";
                var details = "HTTP " + xhr.status;
                try {
                    var err = JSON.parse(xhr.responseText);
                    msg = err.error || msg;
                    details += "\n" + JSON.stringify(err, null, 2);
                } catch (pe) {
                    details += "\n" + (xhr.responseText || "(empty)");
                }
                setStatus(msg, "error", details);
                $confirm.prop("disabled", false).text("Confirm Purge");
            }
        });
    }

    // Purge button opens modal (delegated  -  survives re-render)
    $(document).on("click", "#btn_purge", function(e) {
        e.preventDefault();
        var index = tokens.get("target_index") || "synthetic_cim";
        openPurgeModal(index);
    });

    // Modal: cancel
    $(document).on("click", "#purge_modal_cancel", function() {
        closePurgeModal();
    });

    // Modal: close on overlay click
    $(document).on("click", "#purge_modal_overlay", function(e) {
        if (e.target === this) closePurgeModal();
    });

    // Modal: confirm purge
    $(document).on("click", "#purge_modal_confirm", function() {
        var index = $("#purge_modal_index").text();
        executePurge(index);
    });
});
