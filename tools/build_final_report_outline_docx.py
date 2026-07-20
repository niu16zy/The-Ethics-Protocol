from __future__ import annotations

import copy
import html
import shutil
import zipfile
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DOCX = Path(r"C:\Users\admin\Downloads\Final Report MSWord Template (7CCSMPRJ).docx")
OUTPUT_DOCX = ROOT / "output" / "Final Report MSWord Template (7CCSMPRJ).docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def qn(name: str) -> str:
    return f"{{{W}}}{name}"


PROJECT_TITLE = (
    "An AI-Powered Gamified Learning System with Persona-Driven NPCs "
    "for AI Ethics Education"
)


def text_of(element: etree._Element) -> str:
    return "".join(element.xpath(".//w:t/text()", namespaces=NS)).strip()


def set_text(element: etree._Element, text: str) -> None:
    texts = element.xpath(".//w:t", namespaces=NS)
    if texts:
        texts[0].text = text
        for node in texts[1:]:
            node.text = ""
        return
    run = etree.SubElement(element, qn("r"))
    t = etree.SubElement(run, qn("t"))
    t.text = text


def para(style: str | None, text: str = "", *, page_break_before: bool = False) -> etree._Element:
    p = etree.Element(qn("p"))
    ppr = etree.SubElement(p, qn("pPr"))
    if style:
        pstyle = etree.SubElement(ppr, qn("pStyle"))
        pstyle.set(qn("val"), style)
    if page_break_before:
        pb = etree.SubElement(ppr, qn("pageBreakBefore"))
        pb.set(qn("val"), "1")
    if text:
        run = etree.SubElement(p, qn("r"))
        t = etree.SubElement(run, qn("t"))
        if text.startswith(" ") or text.endswith(" "):
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        t.text = text
    return p


def blank() -> etree._Element:
    return para(None, "")


def bullet(text: str, list_ppr: etree._Element | None = None) -> etree._Element:
    p = para("ListParagraph", text)
    if list_ppr is not None:
        ppr = p.find("w:pPr", namespaces=NS)
        num_pr = list_ppr.find("w:numPr", namespaces=NS)
        if ppr is not None and num_pr is not None:
            ppr.insert(0, copy.deepcopy(num_pr))
    return p


def toc_line(text: str, level: int) -> etree._Element:
    return para(f"TOC{level}", text)


def add_section(body: etree._Element, title: str, items: list[str], *, style: str = "Heading2") -> None:
    body.append(para(style, title))
    for item in items:
        body.append(bullet(item))


def add_heading(body: etree._Element, style: str, text: str, *, page_break_before: bool = False) -> None:
    body.append(para(style, text, page_break_before=page_break_before))


def outline_content() -> list[etree._Element]:
    nodes: list[etree._Element] = []
    append = nodes.append

    append(para("Heading1-NoNumber", "Acknowledgement"))
    append(bullet("Outline-only placeholder: write the final acknowledgement after implementation, evaluation, and supervision support are finalised."))
    append(blank())

    append(para("Heading1-NoNumber", "Abstract"))
    for item in [
        "Final abstract should summarise the educational problem, the AI-powered game concept, and the IBM SkillsBuild AI ethics grounding.",
        "Mention the implemented vertical slice: Level 1 debate with a persona-driven NPC, RAG-grounded evaluator, and Logic Fortress meter.",
        "Report the main evaluation evidence at a high level: retrieval traceability, schema validation, fallback behaviour, and end-to-end turn flow.",
        "End with the principal limitation: this is a prototype, and learning impact requires further user study.",
    ]:
        append(bullet(item))
    append(blank())

    append(para("Heading1-NoNumber", "Nomenclature"))
    for item in [
        "AI - Artificial Intelligence.",
        "API - Application Programming Interface.",
        "BM25 - Best Matching 25 ranking function used for lexical retrieval.",
        "DTO - Data Transfer Object.",
        "FTS5 - SQLite full-text search extension used by the implemented retrieval baseline.",
        "IBM KEP - IBM/KCL project context for the applied educational system.",
        "LLM - Large Language Model.",
        "NPC - Non-Player Character.",
        "RAG - Retrieval-Augmented Generation.",
    ]:
        append(bullet(item))
    append(blank())

    append(para("Heading1-NoNumber", "Contents"))
    toc_entries = [
        (1, "1 Introduction"),
        (2, "1.1 Motivation and Context"),
        (2, "1.2 Problem Statement"),
        (2, "1.3 Aims and Objectives"),
        (2, "1.4 Contributions"),
        (2, "1.5 Report Structure"),
        (1, "2 Problem Description and Requirements"),
        (1, "3 Background and Literature Review"),
        (1, "4 System Design"),
        (1, "5 Implementation"),
        (1, "6 Evaluation and Results"),
        (1, "7 Professional Issues"),
        (1, "8 Conclusions"),
        (1, "9 References"),
        (1, "10 Appendices"),
    ]
    for level, text in toc_entries:
        append(toc_line(text, level))
    append(blank())

    append(para("Heading1-NoNumber", "List of Planned Tables"))
    for item in [
        "Table 1: Retrieval technology comparison: SQLite FTS5/BM25, PostgreSQL with pgvector, and other vector database options.",
        "Table 2: EvaluatorResult schema fields and their educational purpose.",
        "Table 3: Test coverage summary for retrieval, evaluator validation, persona boundary, and end-to-end turn flow.",
    ]:
        append(bullet(item))
    append(blank())

    append(para("Heading1-NoNumber", "List of Planned Figures"))
    for item in [
        "Figure 1: Overall system architecture.",
        "Figure 2: Debate turn sequence from player input to persisted NPC response.",
        "Figure 3: Knowledge and application database separation.",
        "Figure 4: Level 1 user interface screenshots.",
    ]:
        append(bullet(item))
    append(blank())

    add_heading(nodes_container := etree.Element("tmp"), "Heading1", "Introduction", page_break_before=True)
    nodes.extend(list(nodes_container))
    for title, items in [
        ("Motivation and Context", [
            "Open with the education problem: traditional AI ethics content can be passive, while students need practice applying principles to realistic scenarios.",
            "Position the project as a gamified learning system derived from IBM SkillsBuild AI ethics course material.",
            "Keep the tone objective; avoid claiming that gamification automatically improves learning outcomes.",
        ]),
        ("Problem Statement", [
            "Define the gap: open-ended ethical arguments are harder to assess than quizzes, and generic LLM chatbots can hallucinate or provide untraceable feedback.",
            "Explain why the system needs grounding, explainable validation, and a controlled NPC persona rather than a generic chatbot.",
        ]),
        ("Aims and Objectives", [
            "State the aim: build an AI-powered gamified learning prototype with persona-driven NPC debate for AI ethics education.",
            "List objectives: structure course content, retrieve evidence, evaluate arguments, generate NPC dialogue, persist traceable turns, and verify the prototype.",
        ]),
        ("Contributions", [
            "Summarise the implemented contributions: SQLite FTS5/BM25 retrieval baseline, dual-layer LLM design, schema-validated evaluator, persona NPC, and Level 1 playable loop.",
            "Mention the engineering contribution as a vertical slice rather than a complete multi-level product.",
        ]),
        ("Report Structure", [
            "Follow the example report's pattern: introduce the problem, define requirements, review related work, present design, implementation, evaluation, professional issues, and conclusions.",
        ]),
    ]:
        add_section(nodes_container, title, items)
    nodes.extend(list(nodes_container)[1:])

    append(para("Heading1", "Problem Description and Requirements", page_break_before=True))
    sections = [
        ("Educational Problem and Target Users", [
            "Describe the learner as someone practising AI ethics reasoning, not simply answering fixed quiz questions.",
            "Explain the player's in-game role as an algorithmic auditor who must construct evidence-grounded ethical objections.",
        ]),
        ("IBM SkillsBuild Content as Knowledge Source", [
            "Explain that the knowledge base is derived from IBM SkillsBuild AI ethics material, especially principles such as fairness, transparency, accountability, privacy, and robustness.",
            "State that course material must be chunked into structured fields rather than passed to the model as one opaque document.",
        ]),
        ("Game Task and Learning Scenario", [
            "Introduce Level 1: The Hiring Gate, Victor Barrett, and the Aegis-Recruit v4 HR screening AI.",
            "Identify the learning focus: bias testing, fairness safeguards, transparency, explainability, and accountability in high-impact AI deployment.",
        ]),
        ("Functional Requirements", [
            "Cover explicit user creation, session creation, debate turn submission, course evidence retrieval, evaluator JSON generation, NPC response generation, meter update, and turn persistence.",
            "Include frontend display requirements: NPC dialogue, meter change, evidence refs, verdict, confidence, and source diagnostics.",
        ]),
        ("Non-Functional and Safety Requirements", [
            "Discuss traceability, explainability, schema validation, testability, clear frontend/backend separation, and safe fallback when LLM output is unusable.",
            "Include latency expectations as a usability concern, but frame them as prototype targets rather than hard production guarantees.",
        ]),
        ("Scope and Assumptions", [
            "Clarify that the current work is a Level 1 prototype, not a full course-wide product.",
            "State that pgvector and hybrid retrieval are future options, while the implemented baseline is SQLite FTS5/BM25.",
        ]),
    ]
    for title, items in sections:
        add_section(etree.Element("unused"), title, [])
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    append(para("Heading1", "Background and Literature Review", page_break_before=True))
    sections = [
        ("AI Ethics Education", [
            "Review why AI ethics education requires applied reasoning around fairness, bias, transparency, accountability, privacy, robustness, and human oversight.",
            "Use the IBM SkillsBuild course as the project-specific educational grounding, while supporting the discussion with broader literature.",
        ]),
        ("Gamified Learning and Serious Games", [
            "Discuss role-play, narrative framing, feedback loops, and adversarial challenge as mechanisms for engagement.",
            "Compare with game-like AI learning examples carefully, focusing on design lessons rather than direct equivalence.",
        ]),
        ("LLMs in Educational Dialogue", [
            "Explain the benefit of dynamic feedback and persona-driven interaction.",
            "Balance this with risks: hallucination, overconfident judgement, prompt injection, and role drift.",
        ]),
        ("Retrieval-Augmented Generation", [
            "Introduce RAG as a way to ground model behaviour in a trusted corpus.",
            "State that RAG reduces but does not eliminate hallucination risk; evaluation and fallback are still necessary.",
        ]),
        ("Retrieval Technology Options", [
            "Compare lexical retrieval, vector retrieval, and hybrid retrieval at a conceptual level.",
            "Treat PostgreSQL with pgvector as a feasible semantic retrieval implementation for future scale or paraphrase-heavy queries.",
            "Prepare the design rationale for selecting SQLite FTS5/BM25 in the implemented prototype.",
        ]),
        ("LLM-as-a-Judge and Explainable Argument Evaluation", [
            "Review why open-ended argument evaluation cannot rely on simple string matching or multiple-choice grading.",
            "Motivate structured evaluator outputs: verdict, score, confidence, identified principles, missing points, and evidence references.",
        ]),
    ]
    for title, items in sections:
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    append(para("Heading1", "System Design", page_break_before=True))
    sections = [
        ("Overall Architecture", [
            "Describe the React/Vite frontend, FastAPI backend, SQLite knowledge database, SQLite application database, and pluggable LLM client.",
            "Show that the frontend only calls backend APIs and never calls LLM providers directly.",
        ]),
        ("Data Architecture", [
            "Separate the knowledge domain from the application domain.",
            "Knowledge DB: documents and documents_fts for course evidence. App DB: users, game_sessions, turns, progress_saves, achievements, and final_reports.",
        ]),
        ("Retrieval Technology Selection", [
            "Present pgvector as a feasible alternative: embeddings, semantic similarity search, and stronger paraphrase matching for larger corpora.",
            "Explain why SQLite FTS5/BM25 was selected for the current implementation: small structured course corpus, explicit ethics vocabulary, simple deployment, reproducibility, and transparent evidence tracing.",
            "State the final decision clearly: pgvector is a future enhancement; SQLite FTS5/BM25 is the implemented retrieval baseline.",
        ]),
        ("RAG Pipeline Design", [
            "Describe the flow: player input, query cleaning, FTS5/BM25 retrieval, EvidenceRef assembly, evaluator prompt construction, and structured result validation.",
            "Emphasise that strong and partial verdicts require evidence references.",
        ]),
        ("Dual-Layer LLM Architecture", [
            "Evaluator Agent: consumes retrieved evidence and returns schema-validated JSON.",
            "Persona Agent: consumes evaluator output and meter state, then produces NPC dialogue without re-judging facts or accessing the knowledge base.",
        ]),
        ("Game Loop and Logic Fortress Meter", [
            "Explain how verdicts affect score_delta and meter reduction.",
            "Connect the meter to learning feedback: stronger evidence-grounded arguments produce stronger game progress.",
        ]),
        ("Level 1 Scenario Design", [
            "Describe Victor Barrett and Aegis-Recruit v4 as a concrete case for hiring AI bias, transparency, explainability, and accountability.",
            "Explain why a single vertical slice is sufficient to demonstrate the architecture and evaluation loop.",
        ]),
    ]
    for title, items in sections:
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    append(para("Heading1", "Implementation", page_break_before=True))
    sections = [
        ("Backend Implementation", [
            "Summarise FastAPI routes, dependency wiring, service layer, repository layer, and Pydantic schemas.",
            "Keep route handlers separate from business logic where possible.",
        ]),
        ("Knowledge Repository and Retrieval Service", [
            "Describe SQLite FTS5/BM25 search, query cleaning, fallback LIKE search, and the EvidenceRef response shape.",
            "Mention traceable fields: document_id, course, lesson, topic, seq_order, excerpt, and score.",
        ]),
        ("Evaluator Service", [
            "Explain required fields in EvaluatorResult and how schema validation prevents brittle string parsing.",
            "Cover low-confidence fallback for no evidence, invalid JSON, provider failure, or schema failure.",
        ]),
        ("Persona Service", [
            "Explain how Victor Barrett's persona profile shapes language while evaluator output controls factual concessions.",
            "Describe safeguards against out-of-character system language, hidden prompt disclosure, and private meter disclosure.",
        ]),
        ("Orchestration and Turn Persistence", [
            "Trace the implemented turn flow: load session, route turn, retrieve evidence, evaluate, update meter, generate persona response, persist turn, and return frontend response.",
            "Mention persistence of player_input, retrieved_refs, evaluator_json, npc_response, meter_before, meter_after, and timestamp.",
        ]),
        ("Frontend Implementation", [
            "Describe the Level 1 intro scene, debate screen, NPC panel, dialogue box, input area, streaming response, meter, and clue/evidence display.",
            "Explain the level configuration pattern for future levels.",
        ]),
        ("Configuration and Security", [
            "Document environment-based API key configuration and provider abstraction.",
            "Emphasise that secrets and direct model endpoints are not exposed to the frontend.",
        ]),
    ]
    for title, items in sections:
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    append(para("Heading1", "Evaluation and Results", page_break_before=True))
    sections = [
        ("Evaluation Strategy", [
            "Frame evaluation around system correctness, grounding, robustness, and user-facing feedback, not only visual completion.",
            "Use the implemented Level 1 path as the vertical slice for demonstration.",
        ]),
        ("Unit and Integration Testing", [
            "Summarise pytest coverage: API, app database, retrieval, evaluator, persona, LLM status, streaming, turn flow, meter, and conversation context.",
            "Relate each test group to a requirement from the specification chapter.",
        ]),
        ("Retrieval Evaluation", [
            "Check whether FTS5/BM25 returns traceable document references for relevant queries such as fairness, bias, hiring, and transparency.",
            "Discuss retrieval limitations for deeper paraphrase matching, motivating future hybrid retrieval.",
        ]),
        ("Argument Validation Evaluation", [
            "Verify schema-valid evaluator output, score calibration, evidence_refs for supported verdicts, and low-confidence behaviour when evidence is absent.",
            "Show one representative example without turning this outline into a full results section.",
        ]),
        ("Game Flow Evaluation", [
            "Demonstrate a full turn: player argument, retrieved evidence, evaluator verdict, NPC response, and meter before/after.",
            "Evaluate whether the UI makes feedback visible without exposing internal prompts.",
        ]),
        ("Robustness Evaluation", [
            "Cover off-topic input, dialogue-only turns, invalid JSON, LLM failure, missing evidence, and fallback responses.",
            "Explain why safe degradation matters in an educational system.",
        ]),
        ("Limitations", [
            "State that the system is a prototype and currently covers one level.",
            "Acknowledge that educational impact requires user study, and that BM25 may be weaker than vector retrieval for broad semantic paraphrases.",
        ]),
    ]
    for title, items in sections:
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    append(para("Heading1", "Professional Issues", page_break_before=True))
    sections = [
        ("Educational Responsibility", [
            "Discuss the risk of misleading learners and the need for low-confidence or clarification paths when evidence is weak.",
            "Explain why evaluator reasoning must be traceable rather than purely conversational.",
        ]),
        ("Bias and Fairness", [
            "Connect the Level 1 hiring AI scenario to the broader professional duty to identify and mitigate bias.",
            "Avoid presenting the fictional NPC's claims as authoritative facts.",
        ]),
        ("Transparency and Explainability", [
            "Explain why evidence refs, verdict, confidence, and missing points are exposed to the learner.",
            "Relate this to AI accountability in educational software.",
        ]),
        ("Privacy, Security, and Data Minimisation", [
            "Cover user/session data, turn persistence, environment variables, secret handling, and frontend/backend boundaries.",
            "Mention that personal data should not be used for model training in this prototype context.",
        ]),
        ("Professional Conduct", [
            "Relate decisions to BCS/IET-style principles: public interest, honesty about limitations, reliability, and responsible handling of data and AI outputs.",
        ]),
    ]
    for title, items in sections:
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    append(para("Heading1", "Conclusions", page_break_before=True))
    sections = [
        ("Summary of Work", [
            "Summarise the completed prototype as an IBM SkillsBuild-grounded AI ethics debate game with a persona-driven NPC.",
            "Restate the core architecture: structured retrieval, evaluator, persona, meter, persistence, and frontend loop.",
        ]),
        ("Achievement of Objectives", [
            "Map each original objective to implemented evidence: knowledge base, retrieval, evaluator schema, persona dialogue, frontend level, and tests.",
        ]),
        ("Project Limitations", [
            "Keep limitations explicit and fair: single level, limited learner evaluation, provider/fallback differences, and retrieval trade-offs.",
        ]),
        ("Future Work", [
            "Evaluate hybrid BM25 plus pgvector retrieval if the corpus expands or paraphrase-heavy input becomes a priority.",
            "Add more levels, final report generation, richer progress analytics, user study, RAGAS-style evaluation, deployment/authentication, and broader IBM course coverage.",
        ]),
    ]
    for title, items in sections:
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    append(para("Heading1", "References", page_break_before=True))
    for item in [
        "Final references should include AI ethics education, gamified learning or serious games, RAG, LLM-as-a-judge, and IBM SkillsBuild course material.",
        "Use one consistent reference format throughout the final report.",
        "Do not cite implementation claims without evidence from the codebase, tests, or documented design artefacts.",
    ]:
        append(bullet(item))

    append(para("Heading1", "Appendices", page_break_before=True))
    sections = [
        ("Appendix A: API Endpoints", [
            "List user, session, turn, streaming, search, save/resume, report, and LLM status endpoints.",
        ]),
        ("Appendix B: Database and Schema Details", [
            "Include knowledge DB schema, app DB schema, and EvaluatorResult JSON schema.",
        ]),
        ("Appendix C: Example Debate Turn", [
            "Provide one traceable example showing input, retrieved_refs, evaluator_json, NPC response, and meter change.",
        ]),
        ("Appendix D: Testing Evidence", [
            "Summarise pytest results, build checks, and manual verification steps.",
        ]),
        ("Appendix E: User Interface Screenshots", [
            "Include final Level 1 intro, debate, evidence, and resolution screenshots.",
        ]),
    ]
    for title, items in sections:
        append(para("Heading2", title))
        for item in items:
            append(bullet(item))

    return nodes


def patch_document_xml(xml: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml, parser)
    body = root.find("w:body", namespaces=NS)
    if body is None:
        raise RuntimeError("DOCX document.xml has no body.")

    children = list(body)
    list_ppr = None
    for child in children:
        if text_of(child).startswith("IEEE Xplore"):
            ppr = child.find("w:pPr", namespaces=NS)
            if ppr is not None:
                list_ppr = copy.deepcopy(ppr)
            break

    base_bullet = bullet

    def local_bullet(text: str) -> etree._Element:
        return base_bullet(text, list_ppr)

    globals()["bullet"] = local_bullet

    for child in children:
        txt = text_of(child)
        if txt.startswith("7CCSMPRJ/7CCSMUIP"):
            set_text(child, "7CCSMPRJ Individual Project Submission 2025/26")
        elif txt.startswith("Individual Project Submission"):
            set_text(child, "Individual Project Submission 2025/26")
        elif txt == "Project Title":
            set_text(child, PROJECT_TITLE)
        elif txt.startswith("Project Title:"):
            set_text(child, f"Project Title: {PROJECT_TITLE}")
        elif txt.startswith("Name:"):
            set_text(child, "Name: Zhiyu Niu")
        elif txt.startswith("Student Number:"):
            set_text(child, "Student Number: K25017844")
        elif txt.startswith("Degree Programme:"):
            set_text(child, "Degree Programme: Advanced Software Engineering")
        elif txt.startswith("Supervisor") or txt.startswith("Supervisor’s"):
            set_text(child, "Supervisor: Leonardo Magela Cunha")
        elif txt.startswith("Word count:"):
            set_text(child, "Word count: Outline-only planning document")
        elif txt.startswith("This dissertation is submitted"):
            set_text(child, "This dissertation is submitted for the degree of MSc in Advanced Software Engineering")

    cutoff = None
    for index, child in enumerate(list(body)):
        if text_of(child) == "Acknowledgement":
            cutoff = index
            break
    if cutoff is None:
        raise RuntimeError("Could not find Acknowledgement section in template.")

    sect_pr = None
    for child in list(body):
        if etree.QName(child).localname == "sectPr":
            sect_pr = copy.deepcopy(child)
            break

    for child in list(body)[cutoff:]:
        body.remove(child)

    for node in outline_content():
        body.append(node)
    if sect_pr is not None:
        body.append(sect_pr)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def patch_settings_xml(xml: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(xml, parser)
    update = root.find("w:updateFields", namespaces=NS)
    if update is None:
        update = etree.SubElement(root, qn("updateFields"))
    update.set(qn("val"), "true")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def main() -> None:
    OUTPUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    tmp_docx = OUTPUT_DOCX.with_suffix(".tmp.docx")
    shutil.copy2(SOURCE_DOCX, tmp_docx)

    with zipfile.ZipFile(SOURCE_DOCX, "r") as zin, zipfile.ZipFile(tmp_docx, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = patch_document_xml(data)
            elif item.filename == "word/settings.xml":
                data = patch_settings_xml(data)
            zout.writestr(item, data)

    tmp_docx.replace(OUTPUT_DOCX)
    print(html.escape(str(OUTPUT_DOCX)))


if __name__ == "__main__":
    main()
