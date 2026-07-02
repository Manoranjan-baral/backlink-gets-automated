# RAG recall accuracy report

Test set: 15 scored ideas (+65 with no owned pages) · Claude-judged pooled truth.

**recall (full): 0.677** · recall (reachable): 0.836 · recall (core): 0.747 · precision: 0.265 · precision (core): 0.244 · capability gap: 0.201

- **recall_full** — vs all relevant, incl. pages only query-expansion found (harsh).
- **recall_reachable** — vs pages production's own methods surfaced (the *ranking* gap).
- **capability_gap** — share of relevant reachable ONLY via query expansion (a *feature* gap).
- **precision** — share of the catalogue that is relevant (guards against dumping).
- **recall_core / precision_core** — restricted to CORE pages (same intent), the headline that ignores peripheral noise.

## By stratum

| stratum | n | recall_full | recall_reachable | recall_core | precision_core | precision | capability_gap | dense@75 |
|---|---|---|---|---|---|---|---|---|
| entity | 4 | 0.738 | 0.92 | 0.738 | 0.27 | 0.27 | 0.221 | 0.668 |
| fixed50 | 6 | 0.657 | 0.803 | 0.833 | 0.273 | 0.324 | 0.198 | 0.628 |
| comparison | 5 | 0.652 | 0.808 | 0.652 | 0.189 | 0.189 | 0.19 | 0.604 |

## Biggest misses (lowest recall_full first)

- **[entity] Role-by-Role Hiring Kit Library: JD Template + Skills Assessment Rubri** — recall_full 0.229, reachable 0.786, missed 37/48:
    - How to hire a Talent Acquisition Specialist | Testlify (/hiring-guides/talent-acquisition-specialist-hiring/) — pool via ['expand']
    - How to craft effective job descriptions (/craft-effective-job-descriptions/) — pool via ['expand']
    - job description generator (/job-description-generator/) — pool via ['expand']
    - How to develop a job profile? (/develop-a-job-profile/) — pool via ['expand']
    - Key job profile components (/job-profile-components/) — pool via ['expand']
    - 60 Logistics Analyst interview questions to ask job appl (/logistics-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - Medical Coder Hiring Guide (/hiring-guides/medical-coder-hiring-guide/) — pool via ['expand']
    - 60 Quality Assurance Analyst interview questions to ask  (/quality-assurance-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
- **[fixed50] Management & Leadership Skills Assessment Kit: Sample Questions + Scor** — recall_full 0.264, reachable 0.365, missed 53/72:
    - What Is Adaptive Leadership? Definition, Principles, and (/adaptive-leadership/) — pool via ['keyword']
    - How to measure the ROI of your talent management initiat (/how-to-measure-roi-of-talent-management-initiatives/) — pool via ['keyword']
    - How to evaluate candidates’ skills with a business judge (/how-to-evaluate-candidates-skills-with-a-business-judgement-test/) — pool via ['expand']
    - How to hire top talent using project manager test (/how-to-hire-top-talent-using-project-manager-test/) — pool via ['dense', 'expand']
    - How to implement a performance management system? (/implement-a-performance-management-system/) — pool via ['keyword']
    - Insightful Financial Management (/test-library/insightful-financial-management-test/) — pool via ['keyword']
    - Product Management (/test-library/product-management-test/) — pool via ['keyword']
    - Capability assessment tools (/hr-glossary/capability-assessment-tools/) — pool via ['expand']
- **[comparison] Degree vs. Skills & Credential Verification: Decision Guide + Where Sk** — recall_full 0.571, reachable 0.706, missed 9/21:
    - Exploring the benefits of skills-based hiring strategies (/benefits-of-skills-based-hiring/) — pool via ['dense', 'expand']
    - Importance of computer skills tests in job interviews (/importance-of-computer-skills-tests-in-job-interviews/) — pool via ['keyword']
    - Why legal education needs skill-based testing for real-w (/legal-education-skill-based-testing/) — pool via ['keyword']
    - Background Verification (/hr-glossary/background-verification/) — pool via ['expand']
    - Candidate dishonesty: Key red flags (/candidate-dishonesty/) — pool via ['expand']
    - Can a computer skill test predict candidate fit (/computer-skill-test-predict-candidate-fit/) — pool via ['keyword']
    - How online EdD graduates can prove leadership skills wit (/edd-graduates-leadership-skills-assessments/) — pool via ['expand']
    - Verify candidate credibility with background checks and  (/verify-candidate-credibility-with-background-checks-and-references/) — pool via ['dense', 'expand']
- **[fixed50] Time-to-Hire: Definition, Benchmarks, Formula & How Assessments Reduce** — recall_full 0.577, reachable 0.882, missed 11/26:
    - How automated candidate scoring systems improve hiring s (/how-automated-candidate-scoring-systems-improve-hiring-speed/) — pool via ['dense']
    - How long should the hiring process take? (/how-long-should-the-hiring-process-take/) — pool via ['dense', 'expand']
    - Pre-hire assessments for HR and recruitment industry (/pre-hire-assessments-for-hr-and-recruitment-industry/) — pool via ['expand']
    - How to create a recruitment dashboard that drive results (/recruitment-dashboard/) — pool via ['expand']
    - HR KPIs: What are they? Examples & formulas (/hr-kpis/) — pool via ['expand']
    - High-volume hiring trends: What the latest data tells us (/high-volume-hiring-trends/) — pool via ['expand']
    - How to use data and analytics to improve recruitment out (/use-data-and-analytics-to-improve-recruitment-process/) — pool via ['expand']
    - How Pre-Employment Assessments Redefined Skill-Based Hir (/how-pre-employment-assessments-redefined-skill-based-hiring/) — pool via ['expand']
- **[fixed50] Pre-Employment Test-Type & Role Selector Guide: Which Assessment Is Ri** — recall_full 0.585, reachable 0.8, missed 17/41:
    - How to choose the right cognitive ability test for hirin (/how-to-choose-the-right-cognitive-ability-test-for-hiring-top-talent/) — pool via ['expand']
    - What types of pre-hire assessments work best for sales r (/pre-hire-assessments-for-sales/) — pool via ['dense', 'expand']
    - How to assess entry-level candidates with skills assessm (/assess-entry-level-candidates-with-skills-assessment/) — pool via ['dense']
    - What role do data-driven aptitude assessment play in hir (/what-role-do-data-driven-aptitude-assessment-play-in-hiring-success/) — pool via ['expand']
    - Key considerations when selecting or creating hiring ass (/considerations-when-selecting-or-creating-hiring-assessment-test/) — pool via ['expand']
    - Key elements to consider when creating recruitment tests (/elements-to-consider-when-creating-recruitment-tests/) — pool via ['expand']
    - Best Pre-Hire Assessment Platforms for Enterprises: An H (/top-10-pre-hire-assessment-platforms-for-enterprises/) — pool via ['expand']
    - How to maximize hiring success with a comprehension test (/maximize-hiring-success-with-a-comprehension-test/) — pool via ['expand']
- **[comparison] Skills Tests vs Certifications vs Work Experience: Which Hiring Signal** — recall_full 0.593, reachable 0.842, missed 11/27:
    - How to use psychometric tests to predict job performance (/how-to-use-psychometric-tests-to-predict-job-performance/) — pool via ['expand']
    - What does the research say about skills assessment? (/research-about-skills-assessment/) — pool via ['expand']
    - Real-world examples of how SJTs predict job performance (/real-world-examples-of-how-sjts-predict-job-performance/) — pool via ['expand']
    - Importance of computer skills tests in job interviews (/importance-of-computer-skills-tests-in-job-interviews/) — pool via ['keyword']
    - Why legal education needs skill-based testing for real-w (/legal-education-skill-based-testing/) — pool via ['keyword']
    - The benefits of using hiring assessments in the recruitm (/the-benefits-of-using-hiring-assessments-in-the-recruitment-process/) — pool via ['expand']
    - How pre-hiring assessments can help recruiters make bett (/benefits-of-pre-hiring-assessments/) — pool via ['expand']
    - What is criterion-related validity? Definition & importa (/criterion-related-validity/) — pool via ['expand']
- **[comparison] AI vs. Human in Hiring: Decision Framework with Scoring Rubric & Asses** — recall_full 0.667, reachable 0.875, missed 7/21:
    - Know everything about the ethical dimension of AI in rec (/know-about-ethical-dimension-of-ai-in-recruitment/) — pool via ['expand']
    - Is AI a threat to recruiters and HR professionals? (/is-ai-a-threat-to-recruiters-and-hr-professionals/) — pool via ['expand']
    - How AI recruitment can positively improve recruitment (/how-ai-recruitment-can-positively-improve-recruitment/) — pool via ['dense', 'expand']
    - Artificial Intelligence (AI) in HR (/hr-glossary/artificial-intelligence-ai/) — pool via ['expand']
    - AI vs human proctoring: What works best? (/ai-vs-human-proctoring/) — pool via ['keyword']
    - How does generative AI enhance candidate skills assessme (/generative-ai-enhance-candidate-skills-assessments/) — pool via ['expand']
    - Advantages and challenges of implementing generative AI  (/advantages-challenges-of-generative-ai-in-recruitment/) — pool via ['expand']
- **[fixed50] Cognitive Aptitude Tests in Hiring: Validity Evidence, Score Cutoffs, ** — recall_full 0.675, reachable 0.818, missed 13/40:
    - Fluid Intelligence (/test-library/fluid-intelligence/) — pool via ['expand']
    - Top 10 aptitude assessment questions for potential candi (/top-10-aptitude-assessment-questions-for-potential-candidates/) — pool via ['dense', 'expand']
    - Figural Inductive Reasoning (Matrix Patterns) (/test-library/figural-inductive-reasoning-test/) — pool via ['expand']
    - Abstract Reasoning (/test-library/abstract-reasoning/) — pool via ['expand']
    - The benefits of using psychometric tests in the workplac (/the-benefits-of-using-psychometric-tests-in-the-workplace/) — pool via ['expand']
    - 5 benefits of integrating employment assessments into yo (/5-benefits-of-integrating-employment-assessments-into-your-hiring-process/) — pool via ['expand']
    - IQ (/test-library/iq-test/) — pool via ['dense']
    - Computer Skill Tests: Do They Predict Job Performance? (/how-effective-are-computer-skill-tests/) — pool via ['dense']
- **[comparison] Psychometric Tests vs Skills Assessments: Which Actually Predicts Job ** — recall_full 0.69, reachable 0.741, missed 9/29:
    - The impact of employment testing on hiring success (/the-impact-of-employment-testing-on-hiring-success/) — pool via ['dense', 'expand']
    - Competency-based assessment: how to build and use one in (/competency-based-assessment/) — pool via ['expand']
    - Use skill assessments data to make better hiring decisio (/use-skill-assessments-data-to-make-better-hiring/) — pool via ['keyword']
    - Skills assessment platform (/skills-assessment-platform/) — pool via ['keyword']
    - Identify top talent using skill assessments (/identify-top-talent-without-lengthy-interviews-with-skill-assessments/) — pool via ['dense', 'keyword']
    - Best skills assessment question libraries: 3500+ skills  (/best-skills-assessment-question-libraries/) — pool via ['keyword']
    - What is a pre-hire assessment? A complete guide (/what-is-pre-hire-assessment/) — pool via ['dense', 'expand']
    - Common types of employment assessments and when to use t (/common-employment-assessments-and-when-to-use-them/) — pool via ['dense', 'expand']
- **[comparison] Hard Skills vs Soft Skills Assessment Guide: Which to Test, How, and W** — recall_full 0.737, reachable 0.875, missed 5/19:
    - 10 types of pre-employment tests for hiring top talent (/types-of-pre-employment-tests/) — pool via ['dense', 'expand']
    - How to assess technical skills: a recruiter’s cheat shee (/recruiter-cheat-sheet-how-to-assess-technical-roles/) — pool via ['expand']
    - How to assess technical skills effectively for job posit (/how-to-assess-technical-skills/) — pool via ['expand']
    - Skills assessment types (/skills-assessment-types/) — pool via ['dense']
    - How to evaluate problem solving skills of candidates (/importance-of-assessing-problem-solving-skills-in-recruitment-for-innovative-solutions/) — pool via ['expand']
- **[fixed50] Hiring Metrics Master Guide: 20+ KPIs with Benchmarks, Formulas & Asse** — recall_full 0.843, reachable 0.956, missed 8/51:
    - Job Offer Acceptance Rate calculator (/job-offer-acceptance-rate-calculator/) — pool via ['expand']
    - Time to Fill (/hr-glossary/time-to-fill/) — pool via ['dense', 'expand']
    - How to reduce the time to hire: 7 ways to recruit candid (/how-to-reduce-the-time-to-hire/) — pool via ['expand']
    - How to make faster hiring decisions with real-time analy (/make-faster-hiring-decisions-with-real-time-analytics/) — pool via ['dense', 'expand']
    - Sourcing channel efficiency calculator (/sourcing-channel-efficiency-calculator/) — pool via ['expand']
    - 5 benefits of integrating employment assessments into yo (/5-benefits-of-integrating-employment-assessments-into-your-hiring-process/) — pool via ['expand']
    - How Anima Health cut phone interview time by 53% and bro (/customer-success-stories/anima-health/) — pool via ['expand']
    - Cost per hire calculator (/cost-per-hire-calculator/) — pool via ['expand']
- **[entity] Turnover & Attrition Risk Calculator: Build a Flight-Risk Score from A** — recall_full 0.844, reachable 0.931, missed 5/32:
    - Employee retention: What is the cost of losing talent? (/employee-retention-what-is-the-cost-of-losing-talent/) — pool via ['expand']
    - Retention Strategy (/hr-glossary/retention-strategy/) — pool via ['dense', 'expand']
    - Employee Retention (/hr-glossary/employee-retention/) — pool via ['expand']
    - How to use personality test data for employee retention (/how-to-use-personality-test-for-employee-retention/) — pool via ['expand']
    - 25 exit interview questions HR must ask in 2026 (+ the h (/top-must-ask-exit-interview-questions-for-insightful-feedback/) — pool via ['dense', 'expand']
- **[entity] Admin & Receptionist Skills Assessment Guide** — recall_full 0.917, reachable 1.0, missed 2/24:
    - Front Office Manager (/job-description-templates/front-office-manager/) — pool via ['expand']
    - Numeric Data Entry Typing Test (10-Key) (/test-library/numeric-data-entry-typing-test-10-key-test/) — pool via ['expand']
- **[entity] Free MS Office Skills Test (Word + Excel)** — recall_full 0.962, reachable 0.962, missed 1/26:
    - Microsoft Access (/test-library/microsoft-access/) — pool via ['dense']

> Limitation: ground truth = only as complete as the pool (dense ∪ Claude-expansion ∪ keyword).
> recall_full includes expansion-only pages the production RAG cannot rank; recall_reachable is the
> fair ranking number. The gap between them is the query-expansion opportunity.