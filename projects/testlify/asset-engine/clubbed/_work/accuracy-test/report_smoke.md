# RAG recall accuracy report (_smoke)

Test set: 20 ideas · Claude-judged pooled ground truth (pool = dense ∪ Claude-expansion ∪ keyword).

**Overall catalogue recall: 0.665**

## By stratum

| stratum | n | catalogue recall | dense@50 | dense@75 | dense@100 |
|---|---|---|---|---|---|
| entity | 4 | 0.682 | 0.52 | 0.607 | 0.675 |
| fixed50 | 5 | 0.749 | 0.563 | 0.713 | 0.808 |
| comparison | 5 | 0.569 | 0.414 | 0.532 | 0.605 |
| random | 0 | None | None | None | None |

## Biggest misses (lowest recall first)

- **[entity] Role-by-Role Hiring Kit Library: JD Template + Skills Assessment Rubri** — recall 0.2222222222222222, missed 42 of 54:
    - How to develop a job profile? (/develop-a-job-profile/) — pool via ['expand']
    - Hiring guides (/hiring-guides/) — pool via ['expand']
    - Project Coordinator Hiring Guide (/hiring-guides/project-coordinator-hiring-guide/) — pool via ['expand']
    - 60 Investment Banking Analyst interview questions to ask j (/investment-banking-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - 60 Business Operations Analyst interview questions to ask  (/business-operations-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - How to craft effective job descriptions (/craft-effective-job-descriptions/) — pool via ['expand']
    - 60 Marketing Analyst interview questions to ask job applic (/marketing-analyst-interview-questions-to-ask-job-applicants/) — pool via ['expand']
    - How to hire a perfect Bookkeeper | Hiring Guide – Testlify (/hiring-guides/bookkeeper-hiring-guide/) — pool via ['expand']
- **[comparison] Psychometric Tests vs Skills Assessments: Which Actually Predicts Job ** — recall 0.45098039215686275, missed 28 of 51:
    - Why a DISC personality test can help you find the best tal (/why-a-disc-personality-test-can-help-you-find-the-best-talent/) — pool via ['expand']
    - Identify top talent using skill assessments (/identify-top-talent-without-lengthy-interviews-with-skill-assessments/) — pool via ['dense', 'expand', 'keyword']
    - Use skill assessments data to make better hiring decisions (/use-skill-assessments-data-to-make-better-hiring/) — pool via ['expand', 'keyword']
    - Using personality tests for hiring – astrology or science? (/using-personality-tests-for-hiring-astrology-or-science/) — pool via ['expand']
    - Enneagram test in hiring: What it is and how to use It (/enneagram-test-and-how-to-use-it/) — pool via ['expand']
    - Pros and cons of personality tests in hiring process (/pros-and-cons-of-personality-tests-in-hiring-process/) — pool via ['expand']
    - Pre-employment DISC personality test: A must-have tool for (/pre-employment-disc-personality-test-a-must-have-tool-for-hiring/) — pool via ['expand']
    - Competency-based assessment: how to build and use one in 2 (/competency-based-assessment/) — pool via ['expand']
- **[comparison] Degree vs. Skills & Credential Verification: Decision Guide + Where Sk** — recall 0.5416666666666666, missed 11 of 24:
    - Background Verification (/hr-glossary/background-verification/) — pool via ['expand']
    - Benefits of skills-based hiring for recruiters (/benefits-of-skills-based-hiring-for-recruiters/) — pool via ['expand']
    - Verify candidate credibility with background checks and re (/verify-candidate-credibility-with-background-checks-and-references/) — pool via ['dense', 'expand']
    - How to assess technical skills effectively for job positio (/how-to-assess-technical-skills/) — pool via ['expand']
    - Is it necessary to verify educational qualifications (/is-it-necessary-to-verify-educational-qualifications/) — pool via ['dense', 'expand']
    - What are the drawbacks of relying solely on resumes in pre (/drawbacks-of-relying-solely-on-resumes-in-pre-hiring/) — pool via ['expand']
    - Importance of computer skills tests in job interviews (/importance-of-computer-skills-tests-in-job-interviews/) — pool via ['keyword']
    - Why legal education needs skill-based testing for real-wor (/legal-education-skill-based-testing/) — pool via ['keyword']
- **[comparison] Skills Tests vs Certifications vs Work Experience: Which Hiring Signal** — recall 0.5483870967741935, missed 14 of 31:
    - What is a pre-hire assessment? A complete guide (/what-is-pre-hire-assessment/) — pool via ['expand']
    - What are the drawbacks of relying solely on resumes in pre (/drawbacks-of-relying-solely-on-resumes-in-pre-hiring/) — pool via ['expand']
    - Importance of computer skills tests in job interviews (/importance-of-computer-skills-tests-in-job-interviews/) — pool via ['keyword']
    - How pre-hiring assessments can help recruiters make better (/benefits-of-pre-hiring-assessments/) — pool via ['expand']
    - Predicting job performance: The Big Five as a recruitment  (/predicting-job-performance-the-big-five-as-a-recruitment-tool/) — pool via ['expand']
    - Why legal education needs skill-based testing for real-wor (/legal-education-skill-based-testing/) — pool via ['keyword']
    - Why skill assessments is essential for recruiters in 2026 (/why-skill-assessments-are-essential-for-recruiters/) — pool via ['expand']
    - What is criterion-related validity? Definition & importanc (/criterion-related-validity/) — pool via ['expand']
- **[comparison] Hard Skills vs Soft Skills Assessment Guide: Which to Test, How, and W** — recall 0.6363636363636364, missed 8 of 22:
    - 10 types of pre-employment tests for hiring top talent (/types-of-pre-employment-tests/) — pool via ['dense']
    - How to assess technical skills effectively for job positio (/how-to-assess-technical-skills/) — pool via ['expand']
    - Capability assessment tools (/hr-glossary/capability-assessment-tools/) — pool via ['expand']
    - Skills assessment types (/skills-assessment-types/) — pool via ['dense']
    - How technical skills assessments enhance candidate evaluat (/how-technical-skills-assessments-enhance-candidate-evaluation/) — pool via ['expand']
    - How to evaluate problem solving skills of candidates (/importance-of-assessing-problem-solving-skills-in-recruitment-for-innovative-solutions/) — pool via ['expand']
    - Why skill-based assessments offer more precision in tech h (/why-skill-based-assessments-offer-more-precision-in-tech-hiring/) — pool via ['expand']
    - How to assess technical skills: a recruiter’s cheat sheet (/recruiter-cheat-sheet-how-to-assess-technical-roles/) — pool via ['expand']
- **[fixed50] Management & Leadership Skills Assessment Kit: Sample Questions + Scor** — recall 0.6551724137931034, missed 10 of 29:
    - Leadership vs. management in project management (/leadership-vs-management-in-project-management/) — pool via ['keyword']
    - Diversity & Inclusion Leadership (/test-library/diversity-inclusion-leadership/) — pool via ['keyword']
    - Management Styles (/hr-glossary/management-styles/) — pool via ['keyword']
    - Management Trainee (/test-library/management-trainee/) — pool via ['keyword']
    - Transformational Leadership (/hr-glossary/transformational-leadership/) — pool via ['keyword']
    - Ethical Leadership (/test-library/ethical-leadership/) — pool via ['keyword']
    - The role of emotional intelligence in leadership and hirin (/role-of-emotional-intelligence-in-leadership-and-hiring/) — pool via ['keyword']
    - Integrating AI into leadership development for a stronger  (/how-ai-shapes-leadership-development-for-a-team/) — pool via ['keyword']
- **[comparison] AI vs. Human in Hiring: Decision Framework with Scoring Rubric & Asses** — recall 0.6666666666666666, missed 7 of 21:
    - Is AI a threat to recruiters and HR professionals? (/is-ai-a-threat-to-recruiters-and-hr-professionals/) — pool via ['expand']
    - How does generative AI enhance candidate skills assessment (/generative-ai-enhance-candidate-skills-assessments/) — pool via ['expand']
    - AI vs human proctoring: What works best? (/ai-vs-human-proctoring/) — pool via ['keyword']
    - Artificial Intelligence (AI) in HR (/hr-glossary/artificial-intelligence-ai/) — pool via ['expand']
    - How AI recruitment can positively improve recruitment (/how-ai-recruitment-can-positively-improve-recruitment/) — pool via ['dense', 'expand']
    - Know everything about the ethical dimension of AI in recru (/know-about-ethical-dimension-of-ai-in-recruitment/) — pool via ['expand']
    - Advantages and challenges of implementing generative AI in (/advantages-challenges-of-generative-ai-in-recruitment/) — pool via ['expand']
- **[fixed50] Pre-Employment Test-Type & Role Selector Guide: Which Assessment Is Ri** — recall 0.6857142857142857, missed 11 of 35:
    - How to choose the right technical assessment tool (/how-to-choose-the-right-technical-assessment-tool/) — pool via ['expand']
    - How to choose the right cognitive ability test for hiring  (/how-to-choose-the-right-cognitive-ability-test-for-hiring-top-talent/) — pool via ['expand']
    - Key considerations when selecting or creating hiring asses (/considerations-when-selecting-or-creating-hiring-assessment-test/) — pool via ['expand']
    - How to use skills assessment to assess for executive roles (/how-to-use-skills-assessment-for-executive-roles/) — pool via ['dense']
    - How to assess entry-level candidates with skills assessmen (/assess-entry-level-candidates-with-skills-assessment/) — pool via ['dense']
    - The different types of psychometric tests and what they me (/types-of-psychometric-tests-and-what-they-measure/) — pool via ['expand']
    - The ultimate guide to candidate assessment (/the-ultimate-guide-to-candidate-assessment/) — pool via ['expand']
    - Psychometric Test (/hr-glossary/psychometric-test-2/) — pool via ['dense', 'expand']
- **[fixed50] Cognitive Aptitude Tests in Hiring: Validity Evidence, Score Cutoffs, ** — recall 0.7297297297297297, missed 10 of 37:
    - Tailoring aptitude tests for specific industries: Best pra (/tailoring-aptitude-tests-for-specific-industries-best-practices/) — pool via ['dense', 'expand']
    - G factor intelligence (/hr-glossary/g-factor/) — pool via ['expand']
    - Abstract Reasoning (/test-library/abstract-reasoning/) — pool via ['expand']
    - Top 10 aptitude assessment questions for potential candida (/top-10-aptitude-assessment-questions-for-potential-candidates/) — pool via ['dense', 'expand']
    - How to evaluate candidates’ skills with a numerical reason (/how-to-evaluate-candidates-skills-with-a-numerical-reasoning-assessment/) — pool via ['dense']
    - Fluid Intelligence (/test-library/fluid-intelligence/) — pool via ['expand']
    - Best Work Aptitude (/test-library/best-work-aptitude/) — pool via ['dense']
    - Logical Reasoning (/test-library/logical-reasoning/) — pool via ['expand']
- **[entity] Admin & Receptionist Skills Assessment Guide** — recall 0.7931034482758621, missed 6 of 29:
    - Front Office Manager (/job-description-templates/front-office-manager/) — pool via ['expand']
    - Organizing skills (/test-library/organizing-skills-test/) — pool via ['dense', 'expand']
    - Seafarers Clerk (/test-library/seafarers-clerk-test/) — pool via ['expand']
    - Numeric Data Entry Typing Test (10-Key) (/test-library/numeric-data-entry-typing-test-10-key-test/) — pool via ['expand']
    - Director of Front Office Operations (/test-library/director-of-front-office-operations-test/) — pool via ['expand']
    - How to create skills assessment tests for different roles (/create-skills-assessment-tests-for-different-roles/) — pool via ['keyword']
- **[entity] Turnover & Attrition Risk Calculator: Build a Flight-Risk Score from A** — recall 0.8181818181818182, missed 6 of 33:
    - Employee retention: What is the cost of losing talent? (/employee-retention-what-is-the-cost-of-losing-talent/) — pool via ['expand']
    - 25 exit interview questions HR must ask in 2026 (+ the hea (/top-must-ask-exit-interview-questions-for-insightful-feedback/) — pool via ['dense', 'expand']
    - Employee Retention (/hr-glossary/employee-retention/) — pool via ['expand']
    - Stay interview (/hr-glossary/stay-interview/) — pool via ['expand']
    - How to use personality test data for employee retention (/how-to-use-personality-test-for-employee-retention/) — pool via ['expand']
    - Retention Strategy (/hr-glossary/retention-strategy/) — pool via ['dense', 'expand']
- **[fixed50] Time-to-Hire: Definition, Benchmarks, Formula & How Assessments Reduce** — recall 0.8333333333333334, missed 3 of 18:
    - How to reduce hiring time without losing seamless integrat (/reduce-hiring-time-without-losing-integrations/) — pool via ['dense']
    - How long should the hiring process take? (/how-long-should-the-hiring-process-take/) — pool via ['dense', 'expand']
    - HR KPIs: What are they? Examples & formulas (/hr-kpis/) — pool via ['expand']
- **[fixed50] Hiring Metrics Master Guide: 20+ KPIs with Benchmarks, Formulas & Asse** — recall 0.84, missed 8 of 50:
    - Sourcing channel efficiency calculator (/sourcing-channel-efficiency-calculator/) — pool via ['expand']
    - How to make faster hiring decisions with real-time analyti (/make-faster-hiring-decisions-with-real-time-analytics/) — pool via ['dense']
    - Time to Fill (/hr-glossary/time-to-fill/) — pool via ['dense', 'expand']
    - Attrition rate calculator (/attrition-rate-calculator/) — pool via ['expand']
    - How to reduce the time to hire: 7 ways to recruit candidat (/how-to-reduce-the-time-to-hire/) — pool via ['expand']
    - Decrease In Time To Hire (/decrease-in-time-to-hire-3/) — pool via ['dense', 'expand']
    - Cost per hire calculator (/cost-per-hire-calculator/) — pool via ['expand']
    - Job Offer Acceptance Rate calculator (/job-offer-acceptance-rate-calculator/) — pool via ['expand']
- **[entity] Free MS Office Skills Test (Word + Excel)** — recall 0.8928571428571429, missed 3 of 28:
    - Digital Literacy (/test-library/digital-literacy-test/) — pool via ['expand']
    - Microsoft Access (/test-library/microsoft-access/) — pool via ['dense']
    - Can a computer skill test predict candidate fit (/computer-skill-test-predict-candidate-fit/) — pool via ['expand']

> Limitation: ground truth is only as complete as the pool; a page no source
> surfaced is invisible. See pool.jsonl for pool sizes/composition.