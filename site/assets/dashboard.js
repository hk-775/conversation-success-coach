(() => {
    "use strict";

    const API = "/api/v1";
    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
    const escapeHtml = (value) =>
        String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    const nowIso = () => new Date().toISOString();
    const formatDate = (value) => {
        if (!value) {
            return "—";
        }
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {
            return value;
        }
        return new Intl.DateTimeFormat(undefined, {
            month: "short",
            day: "numeric",
            hour: "numeric",
            minute: "2-digit",
        }).format(date);
    };

    const modeLabel = (mode) =>
        ({
            sales: "Sales",
            support: "Support",
            recruiting: "Recruiting",
            community: "Community",
        })[mode] || mode;

    const makeSuggestion = (id, mode, category, priority, title, action, example, confidence) => ({
        id,
        category,
        priority,
        title,
        action,
        example_language: example,
        rationale: "This static preview mirrors the explainable local response shape.",
        evidence: [`Mode: ${mode}`],
        confidence,
        limitations: [
            "Heuristic analysis can miss context.",
            "Suggestions require human review and are never sent automatically.",
        ],
        playbook_refs: [`pb_${mode}_preview`],
        requires_human_review: true,
        delivery: "manual_only",
        can_auto_send: false,
    });

    const makeStaticAnalysis = (conversation, score, overrides = {}) => {
        const mode = conversation.mode;
        const fingerprint = "a".repeat(64);
        const modeActions = {
            sales: ["Close the discovery loop", "Answer the pricing question before introducing another ask."],
            support: ["Stabilize and set a checkpoint", "Acknowledge the impact, name the owner, and give a realistic update checkpoint."],
            recruiting: ["Make the process legible", "Answer the remote-policy question and distinguish confirmed timing from estimates."],
            community: ["Moderate the behavior, not the person", "Name the specific behavior, cite the norm, and offer a pause or appeal path."],
        };
        const [title, action] = modeActions[mode];
        return {
            analysis_id: `ana_static_${mode}`,
            conversation_id: conversation.id,
            mode,
            fingerprint,
            created_at: nowIso(),
            overall_score: score,
            status: score >= 72 ? "healthy" : score >= 46 ? "watch" : "at_risk",
            signals: {
                momentum: { score: overrides.momentum || 61, label: "steady", explanation: "Turn balance and open loops.", evidence: ["Static preview"], confidence: 0.76 },
                tone: { score: overrides.tone || 55, label: "neutral", explanation: "Observable language cues only.", evidence: ["Static preview"], confidence: 0.72 },
                clarity: { score: overrides.clarity || 70, label: "clear", explanation: "Specificity and sentence structure.", evidence: ["Static preview"], confidence: 0.72 },
                empathy: { score: overrides.empathy || 48, label: "thin", explanation: "Explicit acknowledgment of stated impact.", evidence: ["Static preview"], confidence: 0.68 },
            },
            unanswered_questions: overrides.questions || [],
            risks: overrides.risks || [],
            suggestions: [
                makeSuggestion(`sug_static_${mode}_1`, mode, "answer_open_question", "now", "Answer the open loop directly", action, `Draft to adapt: “I want to answer that directly and keep the next step transparent.”`, 0.84),
                makeSuggestion(`sug_static_${mode}_2`, mode, "mode_next_step", "next", title, action, "Draft to adapt before using in your normal channel.", 0.79),
                makeSuggestion(`sug_static_${mode}_3`, mode, "clarify_commitment", "optional", "Make the checkpoint checkable", "Use one owner, one action, and one realistic checkpoint.", "Draft to adapt: “I own the next check and will update you by the stated time.”", 0.71),
            ],
            responsible_use: {
                suggestions_only: true,
                requires_human_review: true,
                can_auto_send: false,
                impersonation_allowed: false,
                protected_attribute_inference_allowed: false,
                blocked_capabilities: [],
                behavior: "standard",
                explanation: "Coaching is advisory only and never sends messages.",
            },
            limitations: [
                "Static preview: start the local API for stateful behavior.",
                "Tone and empathy describe observable language, not hidden emotion.",
            ],
            persisted: false,
            expires_at: null,
        };
    };

    const buildStaticStore = () => {
        const conversations = [
            {
                id: "conv_support_bluebird",
                title: "Bluebird export incident",
                mode: "support",
                owner: "Imani Cole",
                participant_label: "Rowan Hart",
                goal: "Restore export access and establish a trustworthy update cadence.",
                stage: "Escalated investigation",
                status: "active",
                is_demo: true,
                created_at: nowIso(),
                updated_at: nowIso(),
                turn_count: 4,
                turns: [
                    { id: "s1", position: 0, speaker: "Rowan Hart", role: "participant", text: "The CSV export has failed three times since the update. This is blocking our board deadline and I am frustrated.", created_at: nowIso() },
                    { id: "s2", position: 1, speaker: "Imani Cole", role: "operator", text: "Can you share the job ID and browser version?", created_at: nowIso() },
                    { id: "s3", position: 2, speaker: "Rowan Hart", role: "participant", text: "Job 48317, Firefox 128. I already sent this yesterday. When will someone own the fix?", created_at: nowIso() },
                    { id: "s4", position: 3, speaker: "Imani Cole", role: "operator", text: "I can see the previous ticket. I am checking whether the export worker retried after the release.", created_at: nowIso() },
                ],
            },
            {
                id: "conv_sales_northstar",
                title: "Northstar analytics discovery",
                mode: "sales",
                owner: "Maya Chen",
                participant_label: "Theo Brooks",
                goal: "Determine fit and agree on a transparent technical next step.",
                stage: "Discovery",
                status: "active",
                is_demo: true,
                created_at: nowIso(),
                updated_at: nowIso(),
                turn_count: 3,
                turns: [
                    { id: "s5", position: 0, speaker: "Maya Chen", role: "operator", text: "Which part is creating the most rework?", created_at: nowIso() },
                    { id: "s6", position: 1, speaker: "Theo Brooks", role: "participant", text: "How would migration work, and what does pricing look like for 40 analysts?", created_at: nowIso() },
                    { id: "s7", position: 2, speaker: "Maya Chen", role: "operator", text: "Migration usually starts with a read-only schema review.", created_at: nowIso() },
                ],
            },
            {
                id: "conv_recruiting_harborline",
                title: "Harborline engineering screen",
                mode: "recruiting",
                owner: "Jordan Vale",
                participant_label: "Nia Mercer",
                goal: "Give the candidate an accurate, fair view of the role and process.",
                stage: "Post-screen follow-up",
                status: "active",
                is_demo: true,
                created_at: nowIso(),
                updated_at: nowIso(),
                turn_count: 3,
                turns: [
                    { id: "s8", position: 0, speaker: "Nia Mercer", role: "participant", text: "Is the role fully remote, and what is the interview timeline from here?", created_at: nowIso() },
                    { id: "s9", position: 1, speaker: "Jordan Vale", role: "operator", text: "The panel review is Tuesday, and I expect an update within two business days.", created_at: nowIso() },
                    { id: "s10", position: 2, speaker: "Nia Mercer", role: "participant", text: "The remote policy is important before I schedule the next stage.", created_at: nowIso() },
                ],
            },
            {
                id: "conv_community_cedar",
                title: "Cedar Commons heated thread",
                mode: "community",
                owner: "Sam Ortiz",
                participant_label: "Cedar Commons members",
                goal: "De-escalate the thread and apply community norms consistently.",
                stage: "Active moderation",
                status: "active",
                is_demo: true,
                created_at: nowIso(),
                updated_at: nowIso(),
                turn_count: 3,
                turns: [
                    { id: "s11", position: 0, speaker: "Drew Lane", role: "participant", text: "Your idea is clueless. I will keep tagging you until you answer.", created_at: nowIso() },
                    { id: "s12", position: 1, speaker: "Sam Ortiz", role: "operator", text: "Please keep the discussion productive.", created_at: nowIso() },
                    { id: "s13", position: 2, speaker: "Avery Moss", role: "participant", text: "Can a moderator explain which rule applies here and whether the thread should pause?", created_at: nowIso() },
                ],
            },
        ];
        conversations[0].latest_analysis = makeStaticAnalysis(conversations[0], 51, {
            empathy: 40,
            questions: [{ question: "When will someone own the fix?", topic: "timeline", asked_by: "Rowan Hart", turn_index: 2, confidence: 0.88 }],
            risks: [{ category: "escalation_or_trust_break", severity: "medium", explanation: "Visible frustration and ownership escalation.", evidence: ["This is blocking our board deadline"], recommended_boundary: "Acknowledge impact and offer a clear escalation path." }],
        });
        conversations[1].latest_analysis = makeStaticAnalysis(conversations[1], 65, {
            questions: [{ question: "What does pricing look like for 40 analysts?", topic: "pricing", asked_by: "Theo Brooks", turn_index: 1, confidence: 0.88 }],
        });
        conversations[2].latest_analysis = makeStaticAnalysis(conversations[2], 69, {
            questions: [{ question: "Is the role fully remote?", topic: "location or remote", asked_by: "Nia Mercer", turn_index: 0, confidence: 0.88 }],
        });
        conversations[3].latest_analysis = makeStaticAnalysis(conversations[3], 34, {
            tone: 31,
            risks: [{ category: "harassment_or_personal_attack", severity: "high", explanation: "Personal labels and repeated unwanted contact are visible.", evidence: ["Your idea is clueless"], recommended_boundary: "Address the behavior and apply published rules consistently." }],
        });
        return {
            conversations,
            playbooks: [
                { id: "pb_support_preview", name: "Impact, ownership, checkpoint", mode: "support", description: "Restore trust during incidents.", principles: ["Acknowledge stated impact.", "Name owner and update checkpoint."], enabled: true, is_demo: true },
                { id: "pb_sales_preview", name: "Transparent discovery", mode: "sales", description: "Advance without pressure.", principles: ["Answer questions before a new ask.", "Use only real deadlines."], enabled: true, is_demo: true },
                { id: "pb_recruiting_preview", name: "Fair candidate process", mode: "recruiting", description: "Keep candidate communication consistent.", principles: ["Use job-relevant criteria.", "Separate facts from estimates."], enabled: true, is_demo: true },
                { id: "pb_community_preview", name: "Behavior-specific moderation", mode: "community", description: "Apply norms consistently.", principles: ["Moderate behavior, not identity.", "Preserve an appeal path."], enabled: true, is_demo: true },
            ],
            feedback: [
                { id: "fb_static_1", kind: "accepted", suggestion_id: "sug_static_support_1", conversation_id: null, outcome: null, created_at: nowIso() },
                { id: "fb_static_2", kind: "outcome", suggestion_id: null, conversation_id: "conv_support_bluebird", outcome: "resolved", created_at: nowIso() },
            ],
            audit: [
                { id: "aud_static_1", event_type: "demo.static_preview", actor: "browser", resource_type: "dataset", resource_id: "static", summary: "Loaded the read-only static preview.", details: { external_calls: 0, content_minimized: true }, created_at: nowIso(), content_minimized: true },
            ],
            privacy: {
                allow_raw_content_storage: false,
                default_analysis_retention_days: 7,
                audit_retention_days: 30,
                updated_at: nowIso(),
                defaults: { ad_hoc_analysis_persisted: false, raw_content_stored: false, audit_contains_transcript_text: false },
            },
        };
    };

    let staticStore = buildStaticStore();
    let staticMode = false;
    const state = {
        conversations: [],
        selectedId: null,
        selected: null,
        analysis: null,
        metrics: null,
        playbooks: [],
        privacy: null,
        audit: [],
        feedback: [],
    };

    const staticMetrics = () => {
        const analyses = staticStore.conversations.map((item) => item.latest_analysis).filter(Boolean);
        const accepted = staticStore.feedback.filter((item) => item.kind === "accepted").length;
        const rejected = staticStore.feedback.filter((item) => item.kind === "rejected").length;
        const outcomes = staticStore.feedback.filter((item) => item.kind === "outcome");
        const averages = {};
        ["momentum", "tone", "clarity", "empathy"].forEach((name) => {
            averages[name] = analyses.length
                ? Math.round(analyses.reduce((sum, item) => sum + item.signals[name].score, 0) / analyses.length)
                : 0;
        });
        return {
            conversations_total: staticStore.conversations.length,
            active_conversations: staticStore.conversations.length,
            analyses_total: analyses.length,
            suggestions_generated: analyses.reduce((sum, item) => sum + item.suggestions.length, 0),
            suggestions_accepted: accepted,
            suggestions_rejected: rejected,
            acceptance_rate: accepted + rejected ? Math.round((accepted / (accepted + rejected)) * 1000) / 10 : 0,
            outcomes_recorded: outcomes.length,
            positive_outcomes: outcomes.filter((item) => ["advanced", "resolved"].includes(item.outcome)).length,
            at_risk_conversations: analyses.filter((item) => item.status === "at_risk").length,
            average_signals: averages,
            mode_breakdown: Object.fromEntries(staticStore.conversations.map((item) => [item.mode, 1])),
            limitations: ["Static preview metrics are illustrative."],
        };
    };

    const staticApi = async (path, options = {}) => {
        const method = (options.method || "GET").toUpperCase();
        const body = options.body ? JSON.parse(options.body) : null;
        if (path === "/health") {
            return { status: "ok", engine: "static-preview", external_network_calls: false, message_delivery_capability: false };
        }
        if (path === "/conversations" && method === "GET") {
            return { items: staticStore.conversations.map(({ turns, ...item }) => ({ ...item, turn_count: turns.length, last_message: turns.at(-1)?.text })) };
        }
        if (path.startsWith("/conversations/") && method === "GET") {
            const id = path.split("/")[2];
            return structuredClone(staticStore.conversations.find((item) => item.id === id));
        }
        if (path.endsWith("/turns") && method === "POST") {
            const id = path.split("/")[2];
            const conversation = staticStore.conversations.find((item) => item.id === id);
            const turn = { id: `turn_static_${Date.now()}`, position: conversation.turns.length, speaker: body.role === "operator" ? conversation.owner : conversation.participant_label, role: body.role, text: body.text, created_at: nowIso() };
            conversation.turns.push(turn);
            conversation.updated_at = nowIso();
            return turn;
        }
        if (path === "/analyze" && method === "POST") {
            const conversation = staticStore.conversations.find((item) => item.id === body.conversation_id) || { id: body.conversation_id, mode: body.mode, turns: body.turns };
            const result = makeStaticAnalysis(conversation, 62);
            conversation.latest_analysis = result;
            return result;
        }
        if (path === "/metrics") {
            return staticMetrics();
        }
        if (path === "/playbooks" && method === "GET") {
            return { items: structuredClone(staticStore.playbooks) };
        }
        if (path === "/playbooks" && method === "POST") {
            const item = { id: `pb_static_${Date.now()}`, ...body, is_demo: false, created_at: nowIso(), updated_at: nowIso() };
            staticStore.playbooks.push(item);
            return item;
        }
        if (path.startsWith("/playbooks/") && method === "PATCH") {
            const id = path.split("/")[2];
            const item = staticStore.playbooks.find((candidate) => candidate.id === id);
            Object.assign(item, body, { updated_at: nowIso() });
            return item;
        }
        if (path === "/privacy/settings" && method === "GET") {
            return structuredClone(staticStore.privacy);
        }
        if (path === "/privacy/settings" && method === "PUT") {
            staticStore.privacy = { ...staticStore.privacy, ...body, updated_at: nowIso() };
            return structuredClone(staticStore.privacy);
        }
        if (path === "/privacy/retention/run") {
            return { status: "completed", deleted: { analyses: 0, conversations: 0, audit: 0 } };
        }
        if (path === "/privacy/purge") {
            if (body.scope === "conversation") {
                staticStore.conversations = staticStore.conversations.filter((item) => item.id !== body.conversation_id);
            }
            return { status: "completed", scope: body.scope, deleted: { conversations: 1 }, audit_retained: true };
        }
        if (path === "/feedback" && method === "GET") {
            return { items: structuredClone(staticStore.feedback) };
        }
        if (path === "/feedback" && method === "POST") {
            const item = { id: `fb_static_${Date.now()}`, ...body, created_at: nowIso() };
            staticStore.feedback.unshift(item);
            return item;
        }
        if (path === "/audit") {
            return { items: structuredClone(staticStore.audit) };
        }
        if (path === "/demo/reset") {
            staticStore = buildStaticStore();
            return { status: "reset", conversations: 4, playbooks: 4, fictional_data: true };
        }
        throw new Error(`Static preview does not implement ${method} ${path}`);
    };

    const detectApi = async () => {
        try {
            const response = await fetch(`${API}/health`, { headers: { Accept: "application/json" }, cache: "no-store" });
            if (!response.ok || !(response.headers.get("content-type") || "").includes("application/json")) {
                throw new Error("Local API unavailable");
            }
            await response.json();
            staticMode = false;
        } catch {
            staticMode = true;
        }
        const dot = $("[data-api-status-dot]");
        const label = $("[data-api-status]");
        dot?.classList.toggle("offline", staticMode);
        if (label) {
            label.textContent = staticMode ? "Static preview · start local API for writes" : "Local deterministic service online";
        }
    };

    const api = async (path, options = {}) => {
        if (staticMode) {
            return staticApi(path, options);
        }
        const response = await fetch(`${API}${path}`, {
            ...options,
            headers: {
                Accept: "application/json",
                ...(options.body ? { "Content-Type": "application/json" } : {}),
                ...(options.headers || {}),
            },
            cache: "no-store",
        });
        if (response.status === 204) {
            return null;
        }
        const contentType = response.headers.get("content-type") || "";
        const payload = contentType.includes("application/json") ? await response.json() : { detail: await response.text() };
        if (!response.ok) {
            const detail = payload.detail || payload.error || payload;
            const message = typeof detail === "string" ? detail : detail.message || JSON.stringify(detail);
            throw new Error(message);
        }
        return payload;
    };

    const toast = (message, error = false) => {
        const region = $("[data-toast-region]");
        const item = document.createElement("div");
        item.className = `toast${error ? " error" : ""}`;
        item.textContent = message;
        region.appendChild(item);
        window.setTimeout(() => item.remove(), 3600);
    };

    const viewMeta = {
        overview: ["Overview", "Seeded local coaching operations"],
        workspace: ["Live workspace", "Analyze observable conversation signals"],
        suggestions: ["Suggestions", "Explainable next-best actions"],
        feedback: ["Outcomes & feedback", "Directional learning, not causality"],
        playbooks: ["Playbooks", "Mode-specific coaching principles"],
        privacy: ["Privacy & safety", "Retention and responsible-use controls"],
        audit: ["Audit history", "Content-minimized state evidence"],
        guided: ["Guided walkthrough", "A meeting-ready product tour"],
    };

    const setView = (view) => {
        $$("[data-view]").forEach((panel) => panel.classList.toggle("active", panel.dataset.view === view));
        $$("[data-view-target]").forEach((button) => button.classList.toggle("active", button.dataset.viewTarget === view));
        const [title, subtitle] = viewMeta[view] || viewMeta.overview;
        $("[data-current-view-title]").textContent = title;
        $("[data-current-view-subtitle]").textContent = subtitle;
        $("#app-sidebar").classList.remove("open");
        $(".mobile-sidebar-button")?.setAttribute("aria-expanded", "false");
        if (view === "audit") {
            refreshAudit();
        }
    };

    const renderScenarioControls = () => {
        const select = $("[data-scenario-select]");
        select.innerHTML = state.conversations
            .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.title)} · ${escapeHtml(modeLabel(item.mode))}</option>`)
            .join("");
        if (state.selectedId) {
            select.value = state.selectedId;
        }
        $("[data-conversation-count]").textContent = state.conversations.length;
        $("[data-list-count]").textContent = state.conversations.length;
        const selectedSummary = state.conversations.find((item) => item.id === state.selectedId);
        if (selectedSummary) {
            const badge = $("[data-mode-badge]");
            badge.textContent = modeLabel(selectedSummary.mode);
            badge.className = `app-badge ${selectedSummary.mode}`;
        }
    };

    const renderConversationList = () => {
        const list = $("[data-conversation-list]");
        list.innerHTML = state.conversations
            .map(
                (item) => `
                    <button class="conversation-item ${item.id === state.selectedId ? "active" : ""}" type="button" data-conversation-id="${escapeHtml(item.id)}">
                        <span class="conversation-item-top">
                            <strong>${escapeHtml(item.title)}</strong>
                            <span class="conversation-mode ${escapeHtml(item.mode)}">${escapeHtml(modeLabel(item.mode))}</span>
                        </span>
                        <p>${escapeHtml(item.last_message || item.goal || "Fictional seeded conversation")}</p>
                        <span class="conversation-item-meta"><span>${Number(item.turn_count || item.turns?.length || 0)} turns</span><span>${escapeHtml(item.latest_analysis?.status || "not analyzed")}</span></span>
                    </button>
                `,
            )
            .join("");
        $$("[data-conversation-id]", list).forEach((button) => {
            button.addEventListener("click", () => selectConversation(button.dataset.conversationId));
        });
    };

    const renderTranscript = () => {
        const conversation = state.selected;
        if (!conversation) {
            return;
        }
        $("[data-conversation-title]").textContent = conversation.title;
        $("[data-conversation-meta]").textContent = `${conversation.owner} · ${conversation.participant_label} · ${conversation.goal}`;
        $("[data-conversation-stage]").textContent = conversation.stage || "Active";
        $("[data-feedback-scope]").textContent = conversation.title;
        const transcript = $("[data-transcript]");
        transcript.innerHTML = (conversation.turns || [])
            .map((turn) => {
                const initials = turn.speaker
                    .split(/\s+/)
                    .map((part) => part[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase();
                return `
                    <div class="chat-row ${turn.role === "operator" ? "operator" : ""}">
                        <span class="chat-avatar">${escapeHtml(initials)}</span>
                        <div class="chat-stack">
                            <div class="chat-author">${escapeHtml(turn.speaker)} · ${escapeHtml(turn.role)}</div>
                            <div class="chat-bubble">${escapeHtml(turn.text)}</div>
                        </div>
                    </div>
                `;
            })
            .join("");
        transcript.scrollTop = transcript.scrollHeight;
    };

    const renderAnalysis = () => {
        const analysis = state.analysis;
        $("[data-suggestion-count]").textContent = analysis?.suggestions?.length || 0;
        if (!analysis) {
            $("[data-overall-score]").textContent = "—";
            $("[data-score-ring]").style.setProperty("--score", "0%");
            $("[data-overall-label]").textContent = "Not analyzed";
            $("[data-overall-detail]").textContent = "Run analysis to see observable signals";
            $("[data-analysis-status]").textContent = "—";
            $("[data-signal-list]").innerHTML = "";
            $("[data-question-list]").innerHTML = '<div class="question-chip">Run analysis to identify open loops.</div>';
            $("[data-risk-list]").innerHTML = '<div class="question-chip">Run analysis to check escalation signals.</div>';
            return;
        }
        $("[data-overall-score]").textContent = analysis.overall_score;
        $("[data-score-ring]").style.setProperty("--score", `${analysis.overall_score}%`);
        $("[data-overall-label]").textContent = analysis.status === "healthy" ? "Healthy" : analysis.status === "watch" ? "Watch closely" : "Needs attention";
        $("[data-overall-detail]").textContent = `${analysis.unanswered_questions.length} open question(s) · ${analysis.risks.length} risk signal(s)`;
        $("[data-analysis-status]").textContent = analysis.status.replace("_", " ");
        const order = ["momentum", "tone", "clarity", "empathy"];
        $("[data-signal-list]").innerHTML = order
            .map((name) => {
                const signal = analysis.signals[name];
                return `
                    <div class="signal-row" title="${escapeHtml(signal.explanation)}">
                        <div class="signal-row-head"><span>${escapeHtml(name[0].toUpperCase() + name.slice(1))} · ${escapeHtml(signal.label)}</span><span>${signal.score}</span></div>
                        <div class="signal-track"><span style="width:${signal.score}%"></span></div>
                    </div>
                `;
            })
            .join("");
        $("[data-question-list]").innerHTML = analysis.unanswered_questions.length
            ? analysis.unanswered_questions
                  .map((item) => `<div class="question-chip"><strong>${escapeHtml(item.topic)}</strong><br>${escapeHtml(item.question)}</div>`)
                  .join("")
            : '<div class="question-chip" style="background:var(--brand-soft);border-color:#c7e4da;color:var(--brand-dark)">No open participant question detected.</div>';
        $("[data-risk-list]").innerHTML = analysis.risks.length
            ? analysis.risks
                  .map((item) => `<div class="risk-chip"><strong>${escapeHtml(item.severity)} · ${escapeHtml(item.category.replaceAll("_", " "))}</strong><br>${escapeHtml(item.recommended_boundary)}</div>`)
                  .join("")
            : '<div class="question-chip" style="background:var(--brand-soft);border-color:#c7e4da;color:var(--brand-dark)">No explicit escalation or sensitive-data signal detected.</div>';
    };

    const renderSuggestions = () => {
        const grid = $("[data-suggestion-grid]");
        const suggestions = state.analysis?.suggestions || [];
        if (!suggestions.length) {
            grid.innerHTML = `
                <div class="dashboard-card empty-state">
                    <span class="empty-state-icon">◇</span>
                    <h3>No suggestions yet</h3>
                    <p>Choose a scenario and run analysis. The coach returns explainable, manual-only next actions.</p>
                    <button class="button button-primary" type="button" data-empty-analyze>Analyze selected scenario</button>
                </div>
            `;
            $("[data-empty-analyze]")?.addEventListener("click", analyzeSelected);
            return;
        }
        grid.innerHTML = suggestions
            .map(
                (item) => `
                    <article class="suggestion-card">
                        <div class="suggestion-priority ${escapeHtml(item.priority)}"><span>●</span>${escapeHtml(item.priority)} · manual only</div>
                        <div class="suggestion-card-body">
                            <span class="suggestion-category">${escapeHtml(item.category.replaceAll("_", " "))}</span>
                            <h3>${escapeHtml(item.title)}</h3>
                            <p class="suggestion-action">${escapeHtml(item.action)}</p>
                            <div class="suggestion-draft"><b>Editable example</b>${escapeHtml(item.example_language)}</div>
                            <div class="suggestion-meta"><span>${item.evidence.length} evidence cue(s)</span><span class="confidence-pill">${Math.round(item.confidence * 100)}% confidence</span></div>
                        </div>
                        <div class="suggestion-actions">
                            <button class="button button-small button-primary" type="button" data-use-suggestion="${escapeHtml(item.id)}">Use as draft</button>
                            <button class="button button-small button-secondary" type="button" data-reject-suggestion="${escapeHtml(item.id)}">Not useful</button>
                        </div>
                    </article>
                `,
            )
            .join("");
        $$("[data-use-suggestion]", grid).forEach((button) => {
            button.addEventListener("click", () => acceptSuggestion(button.dataset.useSuggestion));
        });
        $$("[data-reject-suggestion]", grid).forEach((button) => {
            button.addEventListener("click", () => rejectSuggestion(button.dataset.rejectSuggestion));
        });
    };

    const renderMetrics = () => {
        const metrics = state.metrics;
        if (!metrics) {
            return;
        }
        $("[data-kpi-conversations]").textContent = metrics.active_conversations;
        $("[data-kpi-adoption]").textContent = `${metrics.acceptance_rate}%`;
        $("[data-kpi-outcomes]").textContent = metrics.positive_outcomes;
        $("[data-kpi-risk]").textContent = metrics.at_risk_conversations;
        Object.entries(metrics.average_signals || {}).forEach(([name, value]) => {
            const rounded = Math.round(value);
            const valueNode = $(`[data-chart-value="${name}"]`);
            const bar = $(`[data-chart-bar="${name}"]`);
            if (valueNode) {
                valueNode.textContent = rounded;
            }
            if (bar) {
                window.requestAnimationFrame(() => {
                    bar.style.height = `${rounded}%`;
                });
            }
        });
    };

    const renderActivity = () => {
        const list = $("[data-activity-list]");
        const items = state.audit.slice(0, 6);
        list.innerHTML = items.length
            ? items
                  .map(
                      (item) => `
                        <div class="activity-item">
                            <span class="activity-icon">${item.event_type.includes("privacy") ? "⌁" : item.event_type.includes("feedback") ? "↗" : "◇"}</span>
                            <span class="activity-copy"><strong>${escapeHtml(item.summary)}</strong><span>${escapeHtml(item.event_type)} · ${escapeHtml(formatDate(item.created_at))}</span></span>
                        </div>
                    `,
                  )
                  .join("")
            : '<div class="empty-state" style="min-height:180px"><p>No activity yet.</p></div>';
    };

    const renderFeedback = () => {
        const body = $("[data-feedback-table]");
        body.innerHTML = state.feedback.length
            ? state.feedback
                  .slice(0, 50)
                  .map((item) => {
                      const descriptor = item.outcome || item.suggestion_id || "—";
                      return `
                        <tr>
                            <td><span class="feedback-kind ${escapeHtml(item.kind)}">${escapeHtml(item.kind)}</span></td>
                            <td>${escapeHtml(descriptor)}</td>
                            <td>${escapeHtml(item.conversation_id || "suggestion feedback")}</td>
                            <td>${escapeHtml(formatDate(item.created_at))}</td>
                        </tr>
                    `;
                  })
                  .join("")
            : '<tr><td colspan="4">No feedback records.</td></tr>';
    };

    const renderPlaybooks = () => {
        const grid = $("[data-playbook-grid]");
        grid.innerHTML = state.playbooks
            .map(
                (item) => `
                    <article class="playbook-card">
                        <div class="playbook-head">
                            <div><span class="conversation-mode ${escapeHtml(item.mode)}">${escapeHtml(modeLabel(item.mode))}</span><h3>${escapeHtml(item.name)}</h3><p>${escapeHtml(item.description)}</p></div>
                            <label class="toggle">
                                <input type="checkbox" ${item.enabled ? "checked" : ""} data-playbook-toggle="${escapeHtml(item.id)}">
                                <span class="toggle-track"></span>
                                <span class="sr-only">Enable ${escapeHtml(item.name)}</span>
                            </label>
                        </div>
                        <ul class="principles-mini">${item.principles.map((principle) => `<li>${escapeHtml(principle)}</li>`).join("")}</ul>
                    </article>
                `,
            )
            .join("");
        $$("[data-playbook-toggle]", grid).forEach((toggle) => {
            toggle.addEventListener("change", async () => {
                try {
                    await api(`/playbooks/${toggle.dataset.playbookToggle}`, {
                        method: "PATCH",
                        body: JSON.stringify({ enabled: toggle.checked }),
                    });
                    await refreshPlaybooks();
                    toast(`Playbook ${toggle.checked ? "enabled" : "paused"}.`);
                } catch (error) {
                    toggle.checked = !toggle.checked;
                    toast(error.message, true);
                }
            });
        });
    };

    const renderPrivacy = () => {
        if (!state.privacy) {
            return;
        }
        $("[data-privacy-raw]").checked = state.privacy.allow_raw_content_storage;
        $("[data-privacy-analysis-days]").value = state.privacy.default_analysis_retention_days;
        $("[data-privacy-audit-days]").value = state.privacy.audit_retention_days;
    };

    const renderAudit = () => {
        const body = $("[data-audit-table]");
        body.innerHTML = state.audit.length
            ? state.audit
                  .map(
                      (item) => `
                        <tr>
                            <td><span class="feedback-kind outcome">${escapeHtml(item.event_type)}</span></td>
                            <td>${escapeHtml(item.summary)}</td>
                            <td>${escapeHtml(item.resource_type)}<br><span style="color:var(--muted)">${escapeHtml(item.resource_id || "—")}</span></td>
                            <td class="audit-details">${escapeHtml(JSON.stringify(item.details || {}))}</td>
                            <td>${escapeHtml(formatDate(item.created_at))}</td>
                        </tr>
                    `,
                  )
                  .join("")
            : '<tr><td colspan="5">No audit events.</td></tr>';
    };

    const selectConversation = async (id) => {
        state.selectedId = id;
        renderScenarioControls();
        renderConversationList();
        try {
            state.selected = await api(`/conversations/${encodeURIComponent(id)}`);
            state.analysis = state.selected.latest_analysis || null;
            renderTranscript();
            renderAnalysis();
            renderSuggestions();
            renderConversationList();
        } catch (error) {
            toast(error.message, true);
        }
    };

    const refreshConversations = async () => {
        const response = await api("/conversations");
        state.conversations = response.items || [];
        if (!state.selectedId || !state.conversations.some((item) => item.id === state.selectedId)) {
            const preferred = state.conversations.find((item) => item.id === "conv_support_bluebird");
            state.selectedId = (preferred || state.conversations[0])?.id || null;
        }
        renderScenarioControls();
        renderConversationList();
        if (state.selectedId) {
            await selectConversation(state.selectedId);
        } else {
            state.selected = null;
            state.analysis = null;
            renderAnalysis();
            renderSuggestions();
        }
    };

    const refreshMetrics = async () => {
        state.metrics = await api("/metrics");
        renderMetrics();
    };

    const refreshFeedback = async () => {
        state.feedback = (await api("/feedback?limit=100")).items || [];
        renderFeedback();
    };

    const refreshPlaybooks = async () => {
        state.playbooks = (await api("/playbooks")).items || [];
        renderPlaybooks();
    };

    const refreshPrivacy = async () => {
        state.privacy = await api("/privacy/settings");
        renderPrivacy();
    };

    async function refreshAudit() {
        state.audit = (await api("/audit?limit=100")).items || [];
        renderAudit();
        renderActivity();
    }

    const analyzeSelected = async () => {
        if (!state.selected) {
            toast("Select a conversation first.", true);
            return;
        }
        const buttons = $$("[data-analyze], [data-analyze-from-suggestions]");
        buttons.forEach((button) => {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.textContent = "Analyzing…";
        });
        try {
            const retentionDays = Number(state.privacy?.default_analysis_retention_days || 7);
            const payload = {
                mode: state.selected.mode,
                conversation_id: state.selected.id,
                context: {
                    goal: state.selected.goal || "",
                    stage: state.selected.stage || "",
                    known_facts: [],
                },
                turns: (state.selected.turns || []).map((turn) => ({
                    speaker: turn.speaker,
                    role: turn.role,
                    text: turn.text,
                    timestamp: turn.created_at || turn.timestamp || null,
                })),
                data_handling: {
                    persist_analysis: true,
                    store_raw_content: false,
                    retention_days: Math.max(1, Math.min(30, retentionDays)),
                    consent_confirmed: false,
                },
            };
            state.analysis = await api("/analyze", {
                method: "POST",
                body: JSON.stringify(payload),
            });
            if (state.selected) {
                state.selected.latest_analysis = state.analysis;
            }
            renderAnalysis();
            renderSuggestions();
            await Promise.all([refreshMetrics(), refreshAudit(), refreshConversations()]);
            toast("Analysis refreshed. No message was sent.");
        } catch (error) {
            toast(error.message, true);
        } finally {
            buttons.forEach((button) => {
                button.disabled = false;
                button.textContent = button.dataset.originalText || "Analyze";
            });
        }
    };

    const recordSuggestionFeedback = async (suggestionId, kind) => {
        await api("/feedback", {
            method: "POST",
            body: JSON.stringify({
                kind,
                suggestion_id: suggestionId,
                note: "",
            }),
        });
        await Promise.all([refreshFeedback(), refreshMetrics(), refreshAudit()]);
    };

    const acceptSuggestion = async (suggestionId) => {
        const suggestion = state.analysis?.suggestions.find((item) => item.id === suggestionId);
        if (!suggestion) {
            return;
        }
        try {
            await recordSuggestionFeedback(suggestionId, "accepted");
            try {
                await navigator.clipboard.writeText(suggestion.example_language);
                toast("Editable draft copied. Review it before using your normal channel.");
            } catch {
                toast("Suggestion marked accepted. Copy the editable example manually.");
            }
        } catch (error) {
            toast(error.message, true);
        }
    };

    const rejectSuggestion = async (suggestionId) => {
        try {
            await recordSuggestionFeedback(suggestionId, "rejected");
            toast("Suggestion marked not useful.");
        } catch (error) {
            toast(error.message, true);
        }
    };

    const recordOutcome = async (outcome) => {
        if (!state.selectedId) {
            toast("Select a conversation first.", true);
            return;
        }
        try {
            await api("/feedback", {
                method: "POST",
                body: JSON.stringify({
                    kind: "outcome",
                    conversation_id: state.selectedId,
                    outcome,
                    note: "",
                }),
            });
            await Promise.all([refreshFeedback(), refreshMetrics(), refreshAudit()]);
            toast(`Outcome recorded: ${outcome.replaceAll("_", " ")}.`);
        } catch (error) {
            toast(error.message, true);
        }
    };

    const resetDemo = async () => {
        if (!window.confirm("Reset all local demo changes and restore the four fictional seed scenarios?")) {
            return;
        }
        try {
            await api("/demo/reset", { method: "POST" });
            state.selectedId = "conv_support_bluebird";
            await reloadAll();
            toast("Fictional demo restored to its canonical seed.");
        } catch (error) {
            toast(error.message, true);
        }
    };

    const savePrivacy = async () => {
        try {
            state.privacy = await api("/privacy/settings", {
                method: "PUT",
                body: JSON.stringify({
                    allow_raw_content_storage: $("[data-privacy-raw]").checked,
                    default_analysis_retention_days: Number($("[data-privacy-analysis-days]").value),
                    audit_retention_days: Number($("[data-privacy-audit-days]").value),
                }),
            });
            renderPrivacy();
            await refreshAudit();
            toast("Privacy controls saved.");
        } catch (error) {
            toast(error.message, true);
        }
    };

    const purgeSelected = async () => {
        if (!state.selectedId) {
            toast("Select a conversation first.", true);
            return;
        }
        if (!window.confirm(`Delete transcript and derived records for “${state.selected?.title || state.selectedId}”? A content-free audit receipt remains.`)) {
            return;
        }
        try {
            await api("/privacy/purge", {
                method: "POST",
                body: JSON.stringify({
                    scope: "conversation",
                    conversation_id: state.selectedId,
                    confirm: true,
                }),
            });
            state.selectedId = null;
            await reloadAll();
            toast("Conversation content purged.");
        } catch (error) {
            toast(error.message, true);
        }
    };

    const runRetention = async () => {
        try {
            const result = await api("/privacy/retention/run", { method: "POST" });
            await reloadAll();
            toast(`Retention applied. Deleted ${Object.values(result.deleted || {}).reduce((sum, value) => sum + Number(value || 0), 0)} record(s).`);
        } catch (error) {
            toast(error.message, true);
        }
    };

    const createPlaybook = async (form) => {
        const data = new FormData(form);
        const principles = String(data.get("principles") || "")
            .split("\n")
            .map((item) => item.trim())
            .filter(Boolean);
        try {
            await api("/playbooks", {
                method: "POST",
                body: JSON.stringify({
                    name: data.get("name"),
                    mode: data.get("mode"),
                    description: data.get("description"),
                    principles,
                    enabled: true,
                }),
            });
            $("[data-playbook-dialog]").close();
            form.reset();
            await Promise.all([refreshPlaybooks(), refreshAudit()]);
            toast("Playbook created.");
        } catch (error) {
            toast(error.message, true);
        }
    };

    const reloadAll = async () => {
        await Promise.all([
            refreshConversations(),
            refreshMetrics(),
            refreshFeedback(),
            refreshPlaybooks(),
            refreshPrivacy(),
            refreshAudit(),
        ]);
    };

    const tourSteps = [
        {
            view: "workspace",
            target: "[data-tour='scenario-select']",
            title: "Switch context explicitly",
            copy: "The coach has four named modes. Selecting a scenario changes the mode adapter and retains the same hard responsible-use boundaries.",
            tip: "Start with Bluebird support, then switch to Cedar Commons to show escalation-aware moderation.",
        },
        {
            view: "workspace",
            target: "[data-tour='analyze-button']",
            title: "Run the real deterministic analysis",
            copy: "This calls the local API with the current transcript, persists only the derived analysis, and returns evidence, confidence, limitations, and suggestions.",
            tip: "Point out that adding a local turn never sends it anywhere.",
        },
        {
            view: "suggestions",
            target: "[data-tour='suggestions-nav']",
            title: "Review, edit, or reject",
            copy: "Use as draft copies editable language and records acceptance. Not useful records rejection. Neither action delivers a message.",
            tip: "The API response itself says can_auto_send=false and delivery=manual_only.",
        },
        {
            view: "feedback",
            target: "[data-tour='feedback-nav']",
            title: "Record outcomes carefully",
            copy: "Outcomes are neutral labels for directional playbook learning, not proof of causality and not an employee performance score.",
            tip: "Use advanced or resolved for a positive demo outcome, then watch overview metrics update.",
        },
        {
            view: "privacy",
            target: "[data-tour='privacy-nav']",
            title: "Make the boundaries visible",
            copy: "Show stateless defaults, bounded retention, content-free audit, purge controls, and the six prohibited optimization goals.",
            tip: "Raw content storage is off by default and still requires request-level consent when enabled.",
        },
        {
            view: "guided",
            target: "[data-tour='reset-button']",
            title: "Return to a known meeting state",
            copy: "Reset clears mutable local data and reconstructs the canonical fictional scenarios through the same deterministic engine.",
            tip: "The reset touches only the product SQLite database.",
        },
    ];
    let tourIndex = 0;

    const clearTourHighlight = () => {
        $(".tour-highlight")?.classList.remove("tour-highlight");
    };

    const renderTour = () => {
        const step = tourSteps[tourIndex];
        setView(step.view);
        clearTourHighlight();
        window.setTimeout(() => {
            const target = $(step.target);
            target?.classList.add("tour-highlight");
            target?.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
        }, 80);
        $("[data-tour-title]").textContent = step.title;
        $("[data-tour-copy]").textContent = step.copy;
        $("[data-tour-tip]").textContent = step.tip;
        $("[data-tour-prev]").disabled = tourIndex === 0;
        $("[data-tour-next]").textContent = tourIndex === tourSteps.length - 1 ? "Finish" : "Next";
        $("[data-tour-progress]").innerHTML = tourSteps
            .map((_, index) => `<span class="${index < tourIndex ? "complete" : index === tourIndex ? "active" : ""}"></span>`)
            .join("");
    };

    const startTour = () => {
        tourIndex = 0;
        const dialog = $("[data-tour-dialog]");
        if (!dialog.open) {
            dialog.show();
        }
        renderTour();
    };

    const closeTour = () => {
        clearTourHighlight();
        $("[data-tour-dialog]").close();
    };

    const bindEvents = () => {
        $$("[data-view-target]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewTarget)));
        $$("[data-view-link]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.viewLink)));
        $$("[data-demo-jump]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.demoJump)));
        $$("[data-start-tour]").forEach((button) => button.addEventListener("click", startTour));
        $$("[data-reset-demo]").forEach((button) => button.addEventListener("click", resetDemo));
        $$("[data-analyze]").forEach((button) => button.addEventListener("click", analyzeSelected));
        $("[data-analyze-from-suggestions]").addEventListener("click", analyzeSelected);
        $("[data-scenario-select]").addEventListener("change", (event) => selectConversation(event.target.value));
        $("[data-save-privacy]").addEventListener("click", savePrivacy);
        $("[data-purge-conversation]").addEventListener("click", purgeSelected);
        $("[data-run-retention]").addEventListener("click", runRetention);
        $("[data-refresh-audit]").addEventListener("click", refreshAudit);
        $$("[data-outcome]").forEach((button) => button.addEventListener("click", () => recordOutcome(button.dataset.outcome)));
        $("[data-open-playbook]").addEventListener("click", () => $("[data-playbook-dialog]").showModal());
        $("[data-playbook-form]").addEventListener("submit", (event) => {
            event.preventDefault();
            createPlaybook(event.currentTarget);
        });
        $("[data-turn-form]").addEventListener("submit", async (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const data = new FormData(form);
            const text = String(data.get("text") || "").trim();
            if (!text || !state.selectedId) {
                toast("Enter a fictional local turn first.", true);
                return;
            }
            try {
                await api(`/conversations/${encodeURIComponent(state.selectedId)}/turns`, {
                    method: "POST",
                    body: JSON.stringify({
                        speaker: data.get("role") === "operator" ? state.selected.owner : state.selected.participant_label,
                        role: data.get("role"),
                        text,
                        timestamp: null,
                    }),
                });
                form.reset();
                await refreshConversations();
                toast("Turn added locally. Run analysis when ready.");
            } catch (error) {
                toast(error.message, true);
            }
        });
        $(".mobile-sidebar-button")?.addEventListener("click", (event) => {
            const sidebar = $("#app-sidebar");
            const open = sidebar.classList.toggle("open");
            event.currentTarget.setAttribute("aria-expanded", String(open));
        });
        $("[data-tour-close]").addEventListener("click", closeTour);
        $("[data-tour-prev]").addEventListener("click", () => {
            if (tourIndex > 0) {
                tourIndex -= 1;
                renderTour();
            }
        });
        $("[data-tour-next]").addEventListener("click", () => {
            if (tourIndex >= tourSteps.length - 1) {
                closeTour();
                return;
            }
            tourIndex += 1;
            renderTour();
        });
    };

    const initialize = async () => {
        bindEvents();
        try {
            await detectApi();
            await reloadAll();
        } catch (error) {
            toast(`Dashboard initialization failed: ${error.message}`, true);
        }
    };

    initialize();
})();
