"""Domain curriculum catalog: courses, prerequisite-linked concepts, rich study resources, and assessments."""

COURSES_CATALOG = [
    {
        "code": "AI-101",
        "title": "Mathematical Foundations for Machine Learning",
        "category": "Core Mathematics",
        "difficulty": "Foundational",
        "credit_hours": 4,
        "instructor_name": "Prof. Arvind Krishnan",
        "description": "Vector spaces, eigenvalues, multivariable calculus, Bayesian inference, and numerical optimization for ML.",
        "modules_count": 8,
        "concepts": [
            {
                "code": "MATH-VEC",
                "name": "Linear Algebra & Eigen-Decomposition",
                "difficulty_weight": 0.45,
                "prereq_code": None,
                "description": "Matrix transformations, dot products, norms, rank, eigenvectors, and singular value decomposition (SVD).",
                "key_notes": (
                    "1. Inner product <u, v> = ||u|| ||v|| cos(theta) measures directional alignment.\n"
                    "2. Eigenvalue equation Av = lambda v identifies invariant axes of linear operators.\n"
                    "3. Singular Value Decomposition A = U Sigma V^T generalizes diagonalization to rectangular matrices and underpins PCA and LSA."
                ),
            },
            {
                "code": "MATH-PROB",
                "name": "Probability & Bayesian Inference",
                "difficulty_weight": 0.52,
                "prereq_code": "MATH-VEC",
                "description": "Conditional probability, Bayes rule, likelihood estimation, and conjugate priors.",
                "key_notes": (
                    "1. Bayes Theorem: P(H|D) = P(D|H) * P(H) / P(D), updating prior belief with observed evidence.\n"
                    "2. Maximum Likelihood Estimation (MLE) chooses theta maximizing log P(D|theta), whereas MAP adds a log-prior penalty.\n"
                    "3. Gaussian distributions remain closed under linear projections, making covariance matrices central to multivariate modeling."
                ),
            },
            {
                "code": "MATH-OPT",
                "name": "Gradient Descent & Convex Optimization",
                "difficulty_weight": 0.62,
                "prereq_code": "MATH-VEC",
                "description": "Partial derivatives, Jacobians, step-size stability, momentum, and convex loss landscapes.",
                "key_notes": (
                    "1. Gradient update: theta_{t+1} = theta_t - eta * grad_theta L(theta_t), stepping opposite the steepest ascent direction.\n"
                    "2. Excessively large learning rate eta causes oscillation or divergence; too small slows convergence.\n"
                    "3. Mini-batch SGD trades exact gradient precision for fast per-step updates and escapes shallow saddle points."
                ),
            },
            {
                "code": "MATH-STAT",
                "name": "Hypothesis Testing & Confidence Intervals",
                "difficulty_weight": 0.50,
                "prereq_code": "MATH-PROB",
                "description": "Sampling distributions, p-values, Type I/II errors, and bootstrap confidence intervals.",
                "key_notes": (
                    "1. A 95% confidence interval quantifies estimator uncertainty across repeated samples.\n"
                    "2. Statistical power (1 - beta) increases with sample size and effect magnitude.\n"
                    "3. Paired cross-validation tests (e.g., 5x2cv) prevent false significance claims when comparing classifiers."
                ),
            },
        ],
    },
    {
        "code": "ML-201",
        "title": "Supervised Learning & Model Validation",
        "category": "Machine Learning",
        "difficulty": "Intermediate",
        "credit_hours": 4,
        "instructor_name": "Dr. Meenakshi Iyer",
        "description": "Regression, classification, ensemble methods, regularization, and rigorous generalization evaluation.",
        "modules_count": 10,
        "concepts": [
            {
                "code": "ML-REG",
                "name": "Linear & Logistic Regression",
                "difficulty_weight": 0.48,
                "prereq_code": "MATH-OPT",
                "description": "Ordinary least squares, sigmoid link function, log-loss (binary cross-entropy), and decision boundaries.",
                "key_notes": (
                    "1. Linear regression minimizes MSE = (1/n) sum (y_i - w^T x_i)^2.\n"
                    "2. Logistic regression models P(y=1|x) = sigma(w^T x + b) = 1 / (1 + exp(-w^T x - b)).\n"
                    "3. Binary cross-entropy loss is convex in parameters w, guaranteeing a unique global minimum under gradient descent."
                ),
            },
            {
                "code": "ML-BIAS",
                "name": "Regularization & Bias-Variance Tradeoff",
                "difficulty_weight": 0.68,
                "prereq_code": "ML-REG",
                "description": "Underfitting vs overfitting, L1 Lasso sparsity, L2 Ridge shrinkage, and generalization error decomposition.",
                "key_notes": (
                    "1. Expected test MSE decomposes into Bias^2 + Variance + Irreducible Noise.\n"
                    "2. L2 (Ridge) adds lambda * ||w||_2^2, shrinking correlated weights smoothly without zeroing them.\n"
                    "3. L1 (Lasso) adds lambda * ||w||_1, inducing exact zeros for implicit feature selection."
                ),
            },
            {
                "code": "ML-ENS",
                "name": "Decision Trees & Ensemble Methods",
                "difficulty_weight": 0.64,
                "prereq_code": "ML-BIAS",
                "description": "Gini impurity, entropy splits, bagging (Random Forests), and sequential gradient boosting.",
                "key_notes": (
                    "1. Random Forests reduce variance by averaging decorrelated trees trained on bootstrap samples and random feature subsets.\n"
                    "2. Gradient Boosting reduces bias by fitting each new weak tree to the negative gradient (pseudo-residuals) of prior errors.\n"
                    "3. Max depth, min_samples_leaf, and learning_rate control tree complexity."
                ),
            },
            {
                "code": "ML-EVAL",
                "name": "Cross-Validation & Imbalanced Metrics",
                "difficulty_weight": 0.58,
                "prereq_code": "MATH-STAT",
                "description": "Stratified K-Fold CV, Precision, Recall, F1-score, PR curves, and ROC-AUC interpretation.",
                "key_notes": (
                    "1. Accuracy misleads on imbalanced datasets; always evaluate Precision, Recall, F1, and ROC-AUC.\n"
                    "2. Precision = TP / (TP + FP); Recall = TP / (TP + FN). F1 is their harmonic mean.\n"
                    "3. All scalers and feature selectors must be fit exclusively inside each CV training fold to prevent data leakage."
                ),
            },
        ],
    },
    {
        "code": "ML-204",
        "title": "Unsupervised Learning & Feature Engineering",
        "category": "Data Science",
        "difficulty": "Intermediate",
        "credit_hours": 3,
        "instructor_name": "Prof. Siddharth Nair",
        "description": "Clustering, dimensionality reduction, representation scaling, and text vectorization pipelines.",
        "modules_count": 8,
        "concepts": [
            {
                "code": "UL-KM",
                "name": "K-Means & Cluster Validation",
                "difficulty_weight": 0.55,
                "prereq_code": "MATH-VEC",
                "description": "Lloyd's iterative assignment/update, k-means++ initialization, inertia, and Silhouette score.",
                "key_notes": (
                    "1. K-Means minimizes within-cluster sum of squares (inertia) and requires feature standardization (StandardScaler).\n"
                    "2. Silhouette score ranges from -1 to +1: s(i) = (b(i) - a(i)) / max(a(i), b(i)), measuring cohesion vs separation.\n"
                    "3. Calinski-Harabasz index evaluates the ratio of between-cluster to within-cluster dispersion."
                ),
            },
            {
                "code": "UL-PCA",
                "name": "Principal Component Analysis (PCA)",
                "difficulty_weight": 0.66,
                "prereq_code": "MATH-VEC",
                "description": "Variance maximization, orthogonal projection, explained variance ratio, and noise filtering.",
                "key_notes": (
                    "1. PCA projects centered, scaled data onto top k eigenvectors of the covariance matrix.\n"
                    "2. Explained variance ratio quantifies how much total dataset variance each principal axis preserves.\n"
                    "3. Useful for 2D/3D visualization of high-dimensional learner telemetry and mitigating multicollinearity."
                ),
            },
            {
                "code": "UL-ANOM",
                "name": "Density Estimation & Anomaly Detection",
                "difficulty_weight": 0.70,
                "prereq_code": "MATH-PROB",
                "description": "Isolation Forests, Mahalanobis distance, DBSCAN noise points, and outlier thresholding.",
                "key_notes": (
                    "1. Isolation Forest isolates anomalies faster (shorter average path length) in random partition trees.\n"
                    "2. DBSCAN identifies dense cores via epsilon-neighborhoods and min_samples, labeling sparse points as noise.\n"
                    "3. Z-score thresholds break down in skewed or multimodal feature spaces."
                ),
            },
            {
                "code": "UL-TFIDF",
                "name": "TF-IDF & Lexical Vectorization",
                "difficulty_weight": 0.50,
                "prereq_code": "MATH-VEC",
                "description": "Term frequency weighting, inverse document frequency, n-grams, and cosine retrieval.",
                "key_notes": (
                    "1. TF-IDF(t, d) = tf(t, d) * log((1 + N) / (1 + df(t))) downweights ubiquitous stopwords.\n"
                    "2. L2-normalized TF-IDF vectors enable fast cosine similarity ranking via dot products.\n"
                    "3. Combining unigrams and bigrams captures domain phrases like 'gradient descent' or 'cross validation'."
                ),
            },
        ],
    },
    {
        "code": "DL-301",
        "title": "Deep Neural Networks & Optimization",
        "category": "Deep Learning",
        "difficulty": "Advanced",
        "credit_hours": 4,
        "instructor_name": "Dr. Nandini Deshmukh",
        "description": "Feedforward architectures, backpropagation calculus, stability normalization, and adaptive optimizers.",
        "modules_count": 10,
        "concepts": [
            {
                "code": "DL-MLP",
                "name": "Multilayer Perceptrons & Activations",
                "difficulty_weight": 0.62,
                "prereq_code": "ML-REG",
                "description": "Universal approximation, ReLU, GELU, Sigmoid saturation, and He/Xavier weight initialization.",
                "key_notes": (
                    "1. Non-linear activations allow stacked linear layers to model non-linear decision manifolds.\n"
                    "2. ReLU(z) = max(0, z) prevents positive-region gradient saturation unlike sigmoid/tanh.\n"
                    "3. He initialization scales weights by sqrt(2 / n_in) to preserve activation variance across ReLU layers."
                ),
            },
            {
                "code": "DL-BP",
                "name": "Backpropagation & Gradient Flow",
                "difficulty_weight": 0.80,
                "prereq_code": "DL-MLP",
                "description": "Computational graphs, chain rule accumulation, vanishing/exploding gradients, and residual skip connections.",
                "key_notes": (
                    "1. Backpropagation applies the multivariable chain rule backward from scalar loss L to each layer's weights.\n"
                    "2. Repeated multiplication of derivatives < 1 causes vanishing gradients in deep sigmoid networks.\n"
                    "3. Residual connections y = F(x) + x create an unimpeded identity highway for gradient flow."
                ),
            },
            {
                "code": "DL-NORM",
                "name": "Batch Normalization & Dropout",
                "difficulty_weight": 0.68,
                "prereq_code": "DL-BP",
                "description": "Internal covariate shift stabilization, LayerNorm vs BatchNorm, inverted dropout regularization.",
                "key_notes": (
                    "1. BatchNorm normalizes across the mini-batch dimension and uses running stats at inference.\n"
                    "2. LayerNorm normalizes across feature dimensions per sample, making it batch-size independent for Transformers.\n"
                    "3. Dropout randomly zeroes activations with rate p during training and is disabled at evaluation."
                ),
            },
            {
                "code": "DL-ADAM",
                "name": "Adam Optimizer & LR Scheduling",
                "difficulty_weight": 0.72,
                "prereq_code": "MATH-OPT",
                "description": "Exponential moving averages of first/second moments, bias correction, warmup, and cosine decay.",
                "key_notes": (
                    "1. Adam tracks momentum (m_t) and per-parameter squared gradients (v_t) with bias correction.\n"
                    "2. AdamW decouples L2 weight decay from adaptive gradient scaling for superior generalization.\n"
                    "3. Linear warmup followed by cosine annealing stabilizes early deep network training."
                ),
            },
        ],
    },
    {
        "code": "NLP-305",
        "title": "Transformers & Applied Language Systems",
        "category": "Natural Language Processing",
        "difficulty": "Advanced",
        "credit_hours": 4,
        "instructor_name": "Dr. Vikramaditya Sen",
        "description": "Semantic embeddings, self-attention architectures, retrieval-augmented generation, and evaluation.",
        "modules_count": 8,
        "concepts": [
            {
                "code": "NLP-EMB",
                "name": "Dense Embeddings & Semantic Space",
                "difficulty_weight": 0.60,
                "prereq_code": "UL-TFIDF",
                "description": "Distributed representations, subword tokenization (BPE), and nearest-neighbor vector search.",
                "key_notes": (
                    "1. Dense embeddings map semantically similar phrases to nearby vectors in R^d.\n"
                    "2. Byte-Pair Encoding (BPE) handles rare/compound terms cleanly without out-of-vocabulary failures.\n"
                    "3. Cosine similarity focuses on vector angle, remaining invariant to embedding magnitude."
                ),
            },
            {
                "code": "NLP-ATT",
                "name": "Scaled Dot-Product Self-Attention",
                "difficulty_weight": 0.85,
                "prereq_code": "DL-BP",
                "description": "Queries, Keys, Values, 1/sqrt(d_k) scaling, multi-head projections, and positional encodings.",
                "key_notes": (
                    "1. Attention(Q, K, V) = softmax((Q K^T) / sqrt(d_k)) V.\n"
                    "2. Dividing by sqrt(d_k) prevents large dot products from pushing softmax into tiny-gradient saturation.\n"
                    "3. Multi-head attention lets different heads attend simultaneously to syntactic, coreference, and semantic relations."
                ),
            },
            {
                "code": "NLP-RAG",
                "name": "Retrieval-Augmented Generation (RAG)",
                "difficulty_weight": 0.70,
                "prereq_code": "NLP-EMB",
                "description": "Chunking strategies, hybrid lexical-dense retrieval, grounding, and citation fidelity.",
                "key_notes": (
                    "1. RAG grounds responses in verified external knowledge bases rather than static parametric memory.\n"
                    "2. Hybrid retrieval combines BM25/TF-IDF exact term matching with dense semantic similarity.\n"
                    "3. Explicit source citations enable auditability and prevent hallucinated educational claims."
                ),
            },
            {
                "code": "NLP-FT",
                "name": "Parameter-Efficient Fine-Tuning & Eval",
                "difficulty_weight": 0.78,
                "prereq_code": "NLP-ATT",
                "description": "LoRA low-rank adapters, instruction alignment, faithfulness, and context recall.",
                "key_notes": (
                    "1. LoRA freezes base weights W_0 and learns low-rank updates Delta W = B A where rank r << d.\n"
                    "2. Reduces trainable parameters and optimizer memory by >90% while preserving base knowledge.\n"
                    "3. Evaluation must separately measure retrieval recall and answer groundedness."
                ),
            },
        ],
    },
    {
        "code": "MLO-401",
        "title": "Enterprise MLOps & Production Systems",
        "category": "ML Engineering",
        "difficulty": "Advanced",
        "credit_hours": 3,
        "instructor_name": "Prof. Rohan Kulkarni",
        "description": "Model registries, drift detection, latency SLOs, reproducible training pipelines, and governance.",
        "modules_count": 8,
        "concepts": [
            {
                "code": "MLO-DRIFT",
                "name": "Data Drift & Concept Drift Monitoring",
                "difficulty_weight": 0.65,
                "prereq_code": "ML-EVAL",
                "description": "Population Stability Index (PSI), KS test, covariate shift vs target relationship drift.",
                "key_notes": (
                    "1. Data drift alters P(X) (input distribution), whereas concept drift alters P(Y|X) (decision relationship).\n"
                    "2. PSI < 0.1 indicates stable feature distributions; PSI > 0.25 warrants model retraining.\n"
                    "3. Educational telemetry exhibits seasonal semester shifts requiring scheduled recalibration."
                ),
            },
            {
                "code": "MLO-PIPE",
                "name": "Reproducible Feature & Model Pipelines",
                "difficulty_weight": 0.60,
                "prereq_code": "ML-EVAL",
                "description": "Training-serving skew prevention, sklearn Pipelines, artifact versioning, and deterministic seeds.",
                "key_notes": (
                    "1. Wrapping scalers and estimators inside a unified sklearn Pipeline eliminates training-serving skew.\n"
                    "2. Persist serialized artifacts alongside schema versions and measured CV metrics.\n"
                    "3. Deterministic random seeds guarantee reproducible audits."
                ),
            },
            {
                "code": "MLO-SERV",
                "name": "API Serving & Latency Optimization",
                "difficulty_weight": 0.62,
                "prereq_code": "MLO-PIPE",
                "description": "FastAPI model caching, batch vs real-time inference, P95 latency SLOs, and graceful fallbacks.",
                "key_notes": (
                    "1. Load serialized models once in application memory rather than deserializing per HTTP request.\n"
                    "2. Asynchronous endpoints must offload CPU-heavy model retraining away from request threads.\n"
                    "3. Track P95 inference latency and structured error logs."
                ),
            },
            {
                "code": "MLO-GOV",
                "name": "Algorithmic Fairness & Calibration",
                "difficulty_weight": 0.70,
                "prereq_code": "MLO-DRIFT",
                "description": "Probability calibration (Brier score), subgroup error parity, and human-in-the-loop interventions.",
                "key_notes": (
                    "1. Predicted risk probabilities should align with observed empirical frequencies (calibration curve).\n"
                    "2. Academic risk flags must always provide transparent feature drivers to support advisor judgment.\n"
                    "3. Audit logs record model versions, interventions, and export access for accountability."
                ),
            },
        ],
    },
]

# Assessment question templates mapped by concept code (30 crisp real questions = 5 per course)
ASSESSMENT_QUESTIONS_BY_COURSE = {
    "AI-101": [
        {
            "concept_code": "MATH-VEC",
            "difficulty": "easy",
            "prompt": "If two non-zero feature vectors u and v are orthogonal, what is the value of their cosine similarity?",
            "options": ["1.0", "0.0", "-1.0", "Undefined unless normalized"],
            "correct_index": 1,
            "explanation": "Orthogonal vectors form a 90-degree angle, so cos(90 deg) = 0, making their dot product and cosine similarity 0.",
        },
        {
            "concept_code": "MATH-VEC",
            "difficulty": "medium",
            "prompt": "Which matrix factorization generalizes eigen-decomposition to arbitrary m x n rectangular matrices?",
            "options": ["Cholesky Decomposition", "LU Decomposition", "Singular Value Decomposition (SVD)", "QR Reflection only for square matrices"],
            "correct_index": 2,
            "explanation": "SVD decomposes any m x n real or complex matrix into U * Sigma * V^T, enabling PCA and low-rank approximations.",
        },
        {
            "concept_code": "MATH-PROB",
            "difficulty": "medium",
            "prompt": "In Bayesian parameter estimation, how does Maximum A Posteriori (MAP) estimation differ from Maximum Likelihood Estimation (MLE)?",
            "options": [
                "MAP incorporates a prior distribution P(theta) alongside the likelihood",
                "MLE requires conjugate priors whereas MAP does not",
                "MAP maximizes P(D) independently of parameters",
                "MLE always produces sparse zero weights",
            ],
            "correct_index": 0,
            "explanation": "MAP maximizes P(D|theta)*P(theta), which is equivalent to adding a log-prior regularization term to the MLE objective.",
        },
        {
            "concept_code": "MATH-OPT",
            "difficulty": "medium",
            "prompt": "During gradient descent on a convex quadratic loss, what typically happens if the learning rate eta exceeds 2 / L (where L is the Lipschitz constant of the gradient)?",
            "options": [
                "Convergence accelerates monotonically to zero error",
                "Parameter updates overshoot the minimum and oscillate or diverge",
                "The gradient automatically becomes zero",
                "Momentum cancels out all step sizes",
            ],
            "correct_index": 1,
            "explanation": "When the step size exceeds the curvature stability limit 2/L, each update overshoots the valley and grows in amplitude.",
        },
        {
            "concept_code": "MATH-STAT",
            "difficulty": "hard",
            "prompt": "Why is a paired cross-validation statistical test preferred over comparing a single train-test split accuracy when evaluating two models?",
            "options": [
                "Single splits conflate true model differences with fold sampling variance",
                "Cross-validation eliminates the need for a test metric",
                "Single splits always overestimate recall by 50%",
                "Paired tests automatically double the training dataset size",
            ],
            "correct_index": 0,
            "explanation": "Evaluating across multiple paired folds separates true performance differences from random split variance.",
        },
    ],
    "ML-201": [
        {
            "concept_code": "ML-REG",
            "difficulty": "easy",
            "prompt": "Why does Logistic Regression optimize binary cross-entropy rather than mean squared error with a sigmoid output?",
            "options": [
                "MSE with sigmoid is non-convex and suffers from flat gradients near saturation",
                "Cross-entropy cannot be differentiated analytically",
                "MSE only works for multiclass labels",
                "Cross-entropy removes the need for feature weights",
            ],
            "correct_index": 0,
            "explanation": "Combining sigmoid with MSE yields a non-convex surface with vanishing gradients; log-loss is convex and gives clean linear error gradients.",
        },
        {
            "concept_code": "ML-BIAS",
            "difficulty": "medium",
            "prompt": "Which regularization penalty tends to drive irrelevant feature coefficients to exact zero, performing embedded feature selection?",
            "options": ["L2 Ridge penalty", "L1 Lasso penalty", "Early stopping alone", "StandardScaler normalization"],
            "correct_index": 1,
            "explanation": "The L1 norm diamond constraint intersects coordinate axes at corners, driving weak coefficients exactly to zero.",
        },
        {
            "concept_code": "ML-ENS",
            "difficulty": "medium",
            "prompt": "How do Random Forests reduce prediction variance compared to a single unpruned decision tree?",
            "options": [
                "By fitting trees sequentially to residual errors of previous trees",
                "By averaging decorrelated trees built on bootstrap samples and random feature subsets",
                "By enforcing linear hyperplanes at every node",
                "By removing all depth bounds and averaging identical trees",
            ],
            "correct_index": 1,
            "explanation": "Bagging plus random feature subsampling reduces correlation between trees, lowering ensemble variance.",
        },
        {
            "concept_code": "ML-EVAL",
            "difficulty": "hard",
            "prompt": "In an imbalanced at-risk student dataset (10% positive class), fitting StandardScaler on the entire dataset before 5-fold cross-validation causes:",
            "options": [
                "Data leakage of test fold mean and variance into training folds",
                "Improved generalization on unseen cohorts",
                "Exact equivalence to fitting inside a Pipeline",
                "Zero impact on logistic regression coefficients",
            ],
            "correct_index": 0,
            "explanation": "Global scaling leaks test-fold summary statistics into training; always wrap preprocessing inside an sklearn Pipeline during CV.",
        },
        {
            "concept_code": "ML-EVAL",
            "difficulty": "medium",
            "prompt": "When false negatives (missing an at-risk learner) carry higher institutional cost than false positives, which metric priority is most critical?",
            "options": ["Specificity only", "Recall (Sensitivity) alongside Precision-Recall balance", "Training R-squared", "Raw accuracy"],
            "correct_index": 1,
            "explanation": "High Recall ensures at-risk learners are rarely missed, while monitoring Precision keeps advisor outreach actionable.",
        },
    ],
    "ML-204": [
        {
            "concept_code": "UL-KM",
            "difficulty": "easy",
            "prompt": "Why must numerical features (e.g., weekly study hours [2-25] vs quiz scores [0-100]) be standardized before running K-Means?",
            "options": [
                "Euclidean distance becomes dominated by larger-scale features without scaling",
                "K-Means refuses to run on floating-point numbers",
                "Standardization automatically selects the optimal K",
                "Unscaled features guarantee convex cluster shapes",
            ],
            "correct_index": 0,
            "explanation": "Euclidean distances weight every dimension equally in raw units, so unscaled high-magnitude features dominate cluster assignment.",
        },
        {
            "concept_code": "UL-KM",
            "difficulty": "medium",
            "prompt": "What does a Silhouette score close to +1.0 indicate for a clustered dataset?",
            "options": [
                "Points are tightly cohesive within their assigned cluster and well separated from neighboring clusters",
                "Clusters overlap heavily and centroids are identical",
                "Every point has been assigned to its own singleton cluster",
                "PCA failed to converge",
            ],
            "correct_index": 0,
            "explanation": "Silhouette s(i) = (b - a) / max(a, b) approaches +1 when intra-cluster distance a is small and nearest-cluster distance b is large.",
        },
        {
            "concept_code": "UL-PCA",
            "difficulty": "medium",
            "prompt": "Principal Component Analysis (PCA) determines orthogonal projection axes by:",
            "options": [
                "Maximizing variance captured along ordered eigenvectors of the covariance matrix",
                "Maximizing class label separability using target y",
                "Minimizing L1 sparsity across random subsets",
                "Clustering rows into K centroids first",
            ],
            "correct_index": 0,
            "explanation": "PCA is unsupervised and selects orthogonal eigenvectors corresponding to the largest eigenvalues of the covariance matrix.",
        },
        {
            "concept_code": "UL-ANOM",
            "difficulty": "hard",
            "prompt": "In an Isolation Forest, why do anomalous observations receive higher anomaly scores?",
            "options": [
                "They require fewer random feature splits (shorter tree path length) to become isolated",
                "They always fall into the deepest leaf nodes",
                "They have higher cosine similarity to cluster centers",
                "They increase the training set silhouette score",
            ],
            "correct_index": 0,
            "explanation": "Sparse outlier points sit far from dense clusters and are separated early in random recursive partitioning.",
        },
        {
            "concept_code": "UL-TFIDF",
            "difficulty": "easy",
            "prompt": "What is the primary purpose of the Inverse Document Frequency (IDF) factor in TF-IDF?",
            "options": [
                "To downweight common terms appearing across most documents and emphasize discriminative terms",
                "To sort documents alphabetically",
                "To translate tokens into dense 768-d neural embeddings",
                "To remove punctuation before tokenization",
            ],
            "correct_index": 0,
            "explanation": "IDF scales down ubiquitous vocabulary while preserving high weight for terms concentrated in relevant documents.",
        },
    ],
    "DL-301": [
        {
            "concept_code": "DL-MLP",
            "difficulty": "easy",
            "prompt": "What happens if a 5-layer neural network uses purely linear activation functions f(z) = z between every layer?",
            "options": [
                "The entire network collapses into an equivalent single linear transformation",
                "It achieves universal non-linear approximation faster",
                "Backpropagation stops working completely",
                "Gradient norms grow exponentially at layer 1",
            ],
            "correct_index": 0,
            "explanation": "Composing linear matrix multiplications yields another single matrix multiplication, eliminating non-linear representational power.",
        },
        {
            "concept_code": "DL-BP",
            "difficulty": "hard",
            "prompt": "Why do residual skip connections y = F(x) + x mitigate the vanishing gradient problem in deep networks?",
            "options": [
                "The derivative dy/dx = dF/dx + I adds an identity term allowing gradients to flow directly backward",
                "They replace gradient descent with K-Means updates",
                "They zero out negative weights automatically",
                "They increase sigmoid saturation range",
            ],
            "correct_index": 0,
            "explanation": "The +1 identity term in the Jacobian prevents repeated multiplication by small weights from shrinking early-layer gradients to zero.",
        },
        {
            "concept_code": "DL-BP",
            "difficulty": "medium",
            "prompt": "During backpropagation, how is the gradient with respect to an intermediate hidden layer computed?",
            "options": [
                "By recursively multiplying upstream loss gradients by local layer Jacobians via the chain rule",
                "By perturbing each weight independently in separate forward passes",
                "By taking the second derivative only at the input layer",
                "By averaging all mini-batch labels",
            ],
            "correct_index": 0,
            "explanation": "Reverse-mode automatic differentiation propagates scalar loss sensitivities backward using the chain rule in a single backward sweep.",
        },
        {
            "concept_code": "DL-NORM",
            "difficulty": "medium",
            "prompt": "Why do Transformer architectures favor Layer Normalization over Batch Normalization?",
            "options": [
                "LayerNorm normalizes across features per token independently of batch size and sequence padding",
                "BatchNorm cannot be differentiated",
                "LayerNorm removes all positional information",
                "BatchNorm requires 10x more parameters per layer",
            ],
            "correct_index": 0,
            "explanation": "Variable sequence lengths and small micro-batches make batch statistics noisy; LayerNorm operates cleanly per individual token vector.",
        },
        {
            "concept_code": "DL-ADAM",
            "difficulty": "hard",
            "prompt": "What improvement does AdamW introduce over standard Adam with L2 regularization?",
            "options": [
                "It decouples weight decay from adaptive second-moment gradient scaling",
                "It eliminates momentum entirely",
                "It trains without computing gradients",
                "It fixes the learning rate to 1.0 throughout training",
            ],
            "correct_index": 0,
            "explanation": "In standard Adam, L2 penalties are rescaled by 1/sqrt(v_t); AdamW applies decay directly to weights, improving regularization consistency.",
        },
    ],
    "NLP-305": [
        {
            "concept_code": "NLP-EMB",
            "difficulty": "easy",
            "prompt": "Why do modern language models use subword tokenizers such as Byte-Pair Encoding (BPE) instead of whole-word vocabularies?",
            "options": [
                "To decompose unseen or compound words into known subword units while keeping vocabulary size compact",
                "To avoid using attention masks",
                "To force every sentence to length 10",
                "To eliminate the need for embeddings",
            ],
            "correct_index": 0,
            "explanation": "Subword tokenization avoids out-of-vocabulary UNK tokens while keeping embedding tables manageable.",
        },
        {
            "concept_code": "NLP-ATT",
            "difficulty": "hard",
            "prompt": "In Scaled Dot-Product Attention, softmax((Q K^T) / sqrt(d_k)) V, why do we divide by sqrt(d_k)?",
            "options": [
                "To keep dot-product variance near 1 so softmax does not saturate into tiny gradients as d_k grows",
                "To enforce orthogonality between Queries and Values",
                "To convert cosine similarity into Euclidean distance",
                "To halve memory complexity from O(n^2) to O(n)",
            ],
            "correct_index": 0,
            "explanation": "If Q and K have unit-variance components, their dot product has variance d_k; dividing by sqrt(d_k) restores unit variance before softmax.",
        },
        {
            "concept_code": "NLP-ATT",
            "difficulty": "medium",
            "prompt": "Why does a Transformer require explicit positional encodings added to token embeddings?",
            "options": [
                "Self-attention is permutation-equivariant and has no inherent notion of token order",
                "Positional encodings double the vocabulary size",
                "Without positional encodings, LayerNorm fails with division by zero",
                "Softmax only accepts positive integer inputs",
            ],
            "correct_index": 0,
            "explanation": "Without positional signals, shuffling input tokens produces the same set of pairwise attention interactions.",
        },
        {
            "concept_code": "NLP-RAG",
            "difficulty": "medium",
            "prompt": "What is the key architectural advantage of Hybrid Search (TF-IDF/BM25 + Dense Vector Similarity) in an educational RAG system?",
            "options": [
                "Exact technical acronyms and course codes are matched lexically while conceptual queries match semantically",
                "It eliminates the need to store source documents",
                "It guarantees 0ms latency regardless of corpus size",
                "It disables citation generation",
            ],
            "correct_index": 0,
            "explanation": "Lexical scoring excels on exact identifiers like 'AI-101' or 'AdamW', while dense vectors capture paraphrased concepts.",
        },
        {
            "concept_code": "NLP-FT",
            "difficulty": "medium",
            "prompt": "How does LoRA (Low-Rank Adaptation) dramatically lower GPU memory during fine-tuning?",
            "options": [
                "It freezes pretrained weights and trains small rank-r decomposition matrices B and A",
                "It deletes 90% of transformer attention heads",
                "It quantizes labels to binary integers",
                "It skips validation evaluation",
            ],
            "correct_index": 0,
            "explanation": "Freezing base weights means optimizer states (Adam m, v) are only stored for the tiny low-rank adapter matrices.",
        },
    ],
    "MLO-401": [
        {
            "concept_code": "MLO-DRIFT",
            "difficulty": "medium",
            "prompt": "What distinguishes Concept Drift from Data (Covariate) Drift in an educational risk prediction model?",
            "options": [
                "Concept drift changes the relationship P(Y|X) between behaviors and outcomes, while data drift changes input distribution P(X)",
                "Concept drift only affects categorical strings",
                "Data drift improves accuracy automatically",
                "They are identical terms for missing values",
            ],
            "correct_index": 0,
            "explanation": "For instance, if curriculum changes make study hours affect pass rates differently, P(Y|X) shifts (concept drift).",
        },
        {
            "concept_code": "MLO-PIPE",
            "difficulty": "easy",
            "prompt": "Which practice prevents training-serving skew when deploying a scikit-learn classifier behind a REST API?",
            "options": [
                "Serializing the entire preprocessing + estimator Pipeline together as a single artifact",
                "Re-computing standardization means manually in frontend JavaScript",
                "Fitting a fresh scaler on each single incoming API request",
                "Dropping feature scaling in production",
            ],
            "correct_index": 0,
            "explanation": "Bundling StandardScaler and the model inside one Pipeline guarantees identical feature transformations at train and inference time.",
        },
        {
            "concept_code": "MLO-SERV",
            "difficulty": "medium",
            "prompt": "Why should trained joblib model artifacts be cached in application memory rather than loaded from disk on every API call?",
            "options": [
                "To avoid repeated disk I/O and deserialization overhead that inflates P95 inference latency",
                "Because joblib files delete themselves after one read",
                "To bypass JWT authentication checks",
                "Because SQLite locks the joblib file",
            ],
            "correct_index": 0,
            "explanation": "In-memory model caching reduces per-request inference latency from tens of milliseconds of disk deserialization to sub-millisecond prediction.",
        },
        {
            "concept_code": "MLO-GOV",
            "difficulty": "medium",
            "prompt": "Why should an academic early-warning platform pair risk probabilities with local feature drivers rather than displaying an opaque score alone?",
            "options": [
                "Advisors and learners need actionable, transparent evidence (e.g., attendance vs mastery gap) to design fair interventions",
                "Feature drivers replace the need for evaluation metrics",
                "Opaque scores always violate SQL foreign keys",
                "Local drivers automatically increase ROC-AUC to 1.0",
            ],
            "correct_index": 0,
            "explanation": "Explainable attributions turn risk alerts into concrete pedagogical support rather than black-box labels.",
        },
        {
            "concept_code": "MLO-DRIFT",
            "difficulty": "hard",
            "prompt": "A Population Stability Index (PSI) of 0.31 measured between baseline training features and current semester features indicates:",
            "options": [
                "Significant distribution shift requiring feature audit and scheduled model retraining",
                "Zero shift; distributions are statistically identical",
                "Perfect model calibration",
                "That F1 score has reached 1.0",
            ],
            "correct_index": 0,
            "explanation": "Standard industry thresholds treat PSI < 0.1 as stable, 0.1-0.25 as moderate shift, and > 0.25 as major drift.",
        },
    ],
}
