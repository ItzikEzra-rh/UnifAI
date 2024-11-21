Modular Main Componetns:

1. Separated prompt formatting (GEvalPromptFormatter)
2. Dedicated scoring logic (GEvalScorer)
3. Main evaluation system (GEvalQASystem)

To use this system, you can:

1. Define your evaluation criteria in GEvalConfig.default_config()
2. Adjust weights and scoring thresholds as needed
3. Add new metrics to the EvalMetric enum if required

Depends on the model you are serving, you might need to use the command: huggingface-cli login (in order to be able to use tokenizer)
E.G. if the base model you intend to use for the reviewer is "meta-llama/Llama-3.1-8B-Instruct" please make sure login to HF

Run the reviewer with: (make sure you are located directly under the reviewer folder)
$ python -m g_eval.g_eval_review

** reviewer_questions.json (file details) **

Dictionary structured which provide a specific scoring question for each element under each category in the JSON template.
Each question is designed to elicit a rating from 1 to 100, based on the thoroughness and correctness of the answer in relation to each unique prompt.
Each entry in scoring_questions represents a detailed scoring prompt designed to accurately assess the correctness of an answer in terms
of purpose, clarity, modularity, and reusability specific to each question type.

** Deepeval overview **

1. DeepEval provides pre-implemented metrics (Accuracy, Relevance, Completeness, etc.)
2. Metrics are thoroughly tested and maintained
3. Easier to add new metrics by extending DeepEval's base classes
4. DeepEval provides a structured testing framework with LLMTestCase
5. Better handling of test cases and evaluation results
6. Built-in support for async evaluation
7. DeepEval handles model interactions more robustly
8. Better support for different model types (API, local)
9. Built-in caching and optimization
10. Easier to add custom metrics by extending DeepEval's base classes
11. Better integration with other testing tools
12. More standardized approach to evaluation