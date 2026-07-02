# RAG recall accuracy report (_smoke)

Test set: 14 scored ideas (+6 with no owned pages) · Claude-judged pooled truth.  
_(pre-tier judgments: core/peripheral not available — re-run judge_pool.py for tiers.)_

**recall (full): 0.665** · recall (reachable): 0.863 · precision: 0.261 · capability gap: 0.223

- **recall_full** — vs all relevant, incl. pages only query-expansion found (harsh).
- **recall_reachable** — vs pages production's own methods surfaced (the *ranking* gap).
- **capability_gap** — share of relevant reachable ONLY via query expansion (a *feature* gap).
- **precision** — share of the catalogue that is relevant (guards against dumping).

## By stratum

| stratum | n | recall_full | recall_reachable | precision | capability_gap | dense@75 |
|---|---|---|---|---|---|---|
| entity | 4 | 0.681 | 0.953 | 0.275 | 0.277 | 0.607 |
| fixed50 | 5 | 0.749 | 0.823 | 0.309 | 0.087 | 0.713 |
| comparison | 5 | 0.569 | 0.832 | 0.202 | 0.316 | 0.531 |

## Biggest misses (lowest recall_full first)

- **[entity] Role-by-Role Hiring Kit Library: JD Template + Skills Assessment Rubri** — recall_full 0.222, reachable 1.0, missed 42/54:
    - Types of skills assessment tests (/types-of-skills-assessment-tests/) — pool via ['expand']
    - 60 Trade Support Analyst interview questions to ask job  (/trade-support-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - 60 Marketing Operations Specialist interview questions t (/marketing-operations-specialist-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - Hiring guides (/hiring-guides/) — pool via ['expand']
    - 60 Operations Analyst interview questions to ask job app (/operations-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - 60 Marketing Analyst interview questions to ask job appl (/marketing-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - 60 Medical Coder interview questions to ask job applican (/medical-coder-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - Stellenbeschreibung (/stellenbeschreibung/) — pool via ['expand']
- **[comparison] Psychometric Tests vs Skills Assessments: Which Actually Predicts Job ** — recall_full 0.451, reachable 0.793, missed 28/51:
    - Common types of employment assessments and when to use t (/common-employment-assessments-and-when-to-use-them/) — pool via ['dense', 'expand']
    - Competency-based assessment: how to build and use one in (/competency-based-assessment/) — pool via ['expand']
    - 7 reasons why you should use personality tests in recrui (/reasons-why-you-should-use-personality-tests-in-recruitment/) — pool via ['expand']
    - Using personality tests for hiring – astrology or scienc (/using-personality-tests-for-hiring-astrology-or-science/) — pool via ['expand']
    - Why a DISC personality test can help you find the best t (/why-a-disc-personality-test-can-help-you-find-the-best-talent/) — pool via ['expand']
    - Key benefits of using big five personality test in the r (/key-benefits-of-using-big-five-personality-test-in-the-recruitment-process/) — pool via ['expand']
    - 7 reasons why you should use the DISC personality test i (/reasons-why-you-should-use-the-disc-personality-test-in-recruitment/) — pool via ['expand']
    - How to incorporate personality assessment into your recr (/incorporate-personality-assessment-in-recruitment/) — pool via ['expand']
- **[comparison] Degree vs. Skills & Credential Verification: Decision Guide + Where Sk** — recall_full 0.542, reachable 0.722, missed 11/24:
    - What are the drawbacks of relying solely on resumes in p (/drawbacks-of-relying-solely-on-resumes-in-pre-hiring/) — pool via ['expand']
    - Background Verification (/hr-glossary/background-verification/) — pool via ['expand']
    - Benefits of skills-based hiring for recruiters (/benefits-of-skills-based-hiring-for-recruiters/) — pool via ['expand']
    - Is it necessary to verify educational qualifications (/is-it-necessary-to-verify-educational-qualifications/) — pool via ['dense', 'expand']
    - Why legal education needs skill-based testing for real-w (/legal-education-skill-based-testing/) — pool via ['keyword']
    - Verify candidate credibility with background checks and  (/verify-candidate-credibility-with-background-checks-and-references/) — pool via ['dense', 'expand']
    - Can a computer skill test predict candidate fit (/computer-skill-test-predict-candidate-fit/) — pool via ['expand', 'keyword']
    - How online EdD graduates can prove leadership skills wit (/edd-graduates-leadership-skills-assessments/) — pool via ['expand']
- **[comparison] Skills Tests vs Certifications vs Work Experience: Which Hiring Signal** — recall_full 0.548, reachable 0.895, missed 14/31:
    - How to use psychometric tests to predict job performance (/how-to-use-psychometric-tests-to-predict-job-performance/) — pool via ['expand']
    - What is a pre-hire assessment? A complete guide (/what-is-pre-hire-assessment/) — pool via ['expand']
    - How skills assessments can improve your recruitment proc (/how-skills-assessments-improve-recruitment-process/) — pool via ['expand']
    - What are the drawbacks of relying solely on resumes in p (/drawbacks-of-relying-solely-on-resumes-in-pre-hiring/) — pool via ['expand']
    - How pre-hiring assessments can help recruiters make bett (/benefits-of-pre-hiring-assessments/) — pool via ['expand']
    - Why legal education needs skill-based testing for real-w (/legal-education-skill-based-testing/) — pool via ['keyword']
    - Why skill assessments is essential for recruiters in 202 (/why-skill-assessments-are-essential-for-recruiters/) — pool via ['expand']
    - Importance of computer skills tests in job interviews (/importance-of-computer-skills-tests-in-job-interviews/) — pool via ['keyword']
- **[comparison] Hard Skills vs Soft Skills Assessment Guide: Which to Test, How, and W** — recall_full 0.636, reachable 0.875, missed 8/22:
    - Why skill-based assessments offer more precision in tech (/why-skill-based-assessments-offer-more-precision-in-tech-hiring/) — pool via ['expand']
    - Skills assessment types (/skills-assessment-types/) — pool via ['dense']
    - How to assess technical skills effectively for job posit (/how-to-assess-technical-skills/) — pool via ['expand']
    - 10 types of pre-employment tests for hiring top talent (/types-of-pre-employment-tests/) — pool via ['dense']
    - How to evaluate problem solving skills of candidates (/importance-of-assessing-problem-solving-skills-in-recruitment-for-innovative-solutions/) — pool via ['expand']
    - Capability assessment tools (/hr-glossary/capability-assessment-tools/) — pool via ['expand']
    - How technical skills assessments enhance candidate evalu (/how-technical-skills-assessments-enhance-candidate-evaluation/) — pool via ['expand']
    - How to assess technical skills: a recruiter’s cheat shee (/recruiter-cheat-sheet-how-to-assess-technical-roles/) — pool via ['expand']
- **[fixed50] Management & Leadership Skills Assessment Kit: Sample Questions + Scor** — recall_full 0.655, reachable 0.655, missed 10/29:
    - Management Styles (/hr-glossary/management-styles/) — pool via ['keyword']
    - Management Career Suggestor (/test-library/management-career-suggestor-test/) — pool via ['keyword']
    - Ethical Leadership (/test-library/ethical-leadership/) — pool via ['keyword']
    - Leadership vs. management in project management (/leadership-vs-management-in-project-management/) — pool via ['keyword']
    - The role of emotional intelligence in leadership and hir (/role-of-emotional-intelligence-in-leadership-and-hiring/) — pool via ['keyword']
    - Management Trainee (/test-library/management-trainee/) — pool via ['keyword']
    - Transformational Leadership (/hr-glossary/transformational-leadership/) — pool via ['keyword']
    - Integrating AI into leadership development for a stronge (/how-ai-shapes-leadership-development-for-a-team/) — pool via ['keyword']
- **[comparison] AI vs. Human in Hiring: Decision Framework with Scoring Rubric & Asses** — recall_full 0.667, reachable 0.875, missed 7/21:
    - Is AI a threat to recruiters and HR professionals? (/is-ai-a-threat-to-recruiters-and-hr-professionals/) — pool via ['expand']
    - AI vs human proctoring: What works best? (/ai-vs-human-proctoring/) — pool via ['keyword']
    - How does generative AI enhance candidate skills assessme (/generative-ai-enhance-candidate-skills-assessments/) — pool via ['expand']
    - How AI recruitment can positively improve recruitment (/how-ai-recruitment-can-positively-improve-recruitment/) — pool via ['dense', 'expand']
    - Know everything about the ethical dimension of AI in rec (/know-about-ethical-dimension-of-ai-in-recruitment/) — pool via ['expand']
    - Advantages and challenges of implementing generative AI  (/advantages-challenges-of-generative-ai-in-recruitment/) — pool via ['expand']
    - Artificial Intelligence (AI) in HR (/hr-glossary/artificial-intelligence-ai/) — pool via ['expand']
- **[fixed50] Pre-Employment Test-Type & Role Selector Guide: Which Assessment Is Ri** — recall_full 0.686, reachable 0.8, missed 11/35:
    - Beyond the big five personality test: Exploring niche as (/psychometric-assessments-beyond-big-five-personality-test/) — pool via ['dense']
    - What types of pre-hire assessments work best for sales r (/pre-hire-assessments-for-sales/) — pool via ['dense']
    - How to use skills assessment to assess for executive rol (/how-to-use-skills-assessment-for-executive-roles/) — pool via ['dense']
    - Psychometric Test (/hr-glossary/psychometric-test-2/) — pool via ['dense', 'expand']
    - How to assess entry-level candidates with skills assessm (/assess-entry-level-candidates-with-skills-assessment/) — pool via ['dense']
    - How to choose the right technical assessment tool (/how-to-choose-the-right-technical-assessment-tool/) — pool via ['expand']
    - Pre-Employment Screening: What It Is, Why It Matters, an (/pre-employment-screening-in-hiring-process/) — pool via ['keyword']
    - How to choose the right cognitive ability test for hirin (/how-to-choose-the-right-cognitive-ability-test-for-hiring-top-talent/) — pool via ['expand']
- **[fixed50] Cognitive Aptitude Tests in Hiring: Validity Evidence, Score Cutoffs, ** — recall_full 0.73, reachable 0.844, missed 10/37:
    - Tailoring aptitude tests for specific industries: Best p (/tailoring-aptitude-tests-for-specific-industries-best-practices/) — pool via ['dense', 'expand']
    - Abstract Reasoning (/test-library/abstract-reasoning/) — pool via ['expand']
    - Top 10 aptitude assessment questions for potential candi (/top-10-aptitude-assessment-questions-for-potential-candidates/) — pool via ['dense', 'expand']
    - G factor intelligence (/hr-glossary/g-factor/) — pool via ['expand']
    - Best Work Aptitude (/test-library/best-work-aptitude/) — pool via ['dense']
    - How to evaluate candidates’ skills with a numerical reas (/how-to-evaluate-candidates-skills-with-a-numerical-reasoning-assessment/) — pool via ['dense']
    - Fluid Intelligence (/test-library/fluid-intelligence/) — pool via ['expand']
    - IQ (/test-library/iq-test/) — pool via ['dense', 'expand']
- **[entity] Admin & Receptionist Skills Assessment Guide** — recall_full 0.793, reachable 0.92, missed 6/29:
    - Numeric Data Entry Typing Test (10-Key) (/test-library/numeric-data-entry-typing-test-10-key-test/) — pool via ['expand']
    - Front Office Manager (/job-description-templates/front-office-manager/) — pool via ['expand']
    - Seafarers Clerk (/test-library/seafarers-clerk-test/) — pool via ['expand']
    - Director of Front Office Operations (/test-library/director-of-front-office-operations-test/) — pool via ['expand']
    - How to create skills assessment tests for different role (/create-skills-assessment-tests-for-different-roles/) — pool via ['keyword']
    - Organizing skills (/test-library/organizing-skills-test/) — pool via ['dense', 'expand']
- **[entity] Turnover & Attrition Risk Calculator: Build a Flight-Risk Score from A** — recall_full 0.818, reachable 0.931, missed 6/33:
    - Employee retention: What is the cost of losing talent? (/employee-retention-what-is-the-cost-of-losing-talent/) — pool via ['expand']
    - 25 exit interview questions HR must ask in 2026 (+ the h (/top-must-ask-exit-interview-questions-for-insightful-feedback/) — pool via ['dense', 'expand']
    - How to use personality test data for employee retention (/how-to-use-personality-test-for-employee-retention/) — pool via ['expand']
    - Stay interview (/hr-glossary/stay-interview/) — pool via ['expand']
    - Retention Strategy (/hr-glossary/retention-strategy/) — pool via ['dense', 'expand']
    - Employee Retention (/hr-glossary/employee-retention/) — pool via ['expand']
- **[fixed50] Time-to-Hire: Definition, Benchmarks, Formula & How Assessments Reduce** — recall_full 0.833, reachable 0.882, missed 3/18:
    - HR KPIs: What are they? Examples & formulas (/hr-kpis/) — pool via ['expand']
    - How to reduce hiring time without losing seamless integr (/reduce-hiring-time-without-losing-integrations/) — pool via ['dense']
    - How long should the hiring process take? (/how-long-should-the-hiring-process-take/) — pool via ['dense', 'expand']
- **[fixed50] Hiring Metrics Master Guide: 20+ KPIs with Benchmarks, Formulas & Asse** — recall_full 0.84, reachable 0.933, missed 8/50:
    - Decrease In Time To Hire (/decrease-in-time-to-hire-3/) — pool via ['dense', 'expand']
    - Job Offer Acceptance Rate calculator (/job-offer-acceptance-rate-calculator/) — pool via ['expand']
    - Time to Fill (/hr-glossary/time-to-fill/) — pool via ['dense', 'expand']
    - Sourcing channel efficiency calculator (/sourcing-channel-efficiency-calculator/) — pool via ['expand']
    - Attrition rate calculator (/attrition-rate-calculator/) — pool via ['expand']
    - How to make faster hiring decisions with real-time analy (/make-faster-hiring-decisions-with-real-time-analytics/) — pool via ['dense']
    - Cost per hire calculator (/cost-per-hire-calculator/) — pool via ['expand']
    - How to reduce the time to hire: 7 ways to recruit candid (/how-to-reduce-the-time-to-hire/) — pool via ['expand']
- **[entity] Free MS Office Skills Test (Word + Excel)** — recall_full 0.893, reachable 0.962, missed 3/28:
    - Can a computer skill test predict candidate fit (/computer-skill-test-predict-candidate-fit/) — pool via ['expand']
    - Microsoft Access (/test-library/microsoft-access/) — pool via ['dense']
    - Digital Literacy (/test-library/digital-literacy-test/) — pool via ['expand']

> Limitation: ground truth = only as complete as the pool (dense ∪ Claude-expansion ∪ keyword).
> recall_full includes expansion-only pages the production RAG cannot rank; recall_reachable is the
> fair ranking number. The gap between them is the query-expansion opportunity.