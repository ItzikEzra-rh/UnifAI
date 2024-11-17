Modular Main Componetns:

1. Separated prompt formatting (GEvalPromptFormatter)
2. Dedicated scoring logic (GEvalScorer)
3. Main evaluation system (GEvalQASystem)

To use this system, you can:

1. Define your evaluation criteria in GEvalConfig.default_config()
2. Adjust weights and scoring thresholds as needed
3. Add new metrics to the EvalMetric enum if required

Run the reviewer with: (make sure you are located directly under the reviewer folder)
$ python -m g_eval.g_eval_review

** reviewer_questions.json (file details) **

Dictionary structured which provide a specific scoring question for each element under each category in the JSON template.
Each question is designed to elicit a rating from 1 to 100, based on the thoroughness and correctness of the answer in relation to each unique prompt.
Each entry in scoring_questions represents a detailed scoring prompt designed to accurately assess the correctness of an answer in terms
of purpose, clarity, modularity, and reusability specific to each question type.