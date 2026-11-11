export type UserRole = 'student' | 'admin'

export interface UserSummary {
  id: number
  email: string
  full_name: string
  role: UserRole
  avatar_initials: string
  department: string
  student_profile_id: number | null
  student_code: string | null
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserSummary
}

export interface RiskDriver {
  feature: string
  label: string
  student_value: number
  cohort_mean: number
  impact_score: number
  effect: 'risk_increasing' | 'protective' | 'neutral'
}

export interface TrajectoryPoint {
  week_label: string
  week_number: number
  actual_score: number | null
  projected_score: number | null
  lower_bound: number | null
  upper_bound: number | null
  study_hours: number
  is_forecast: boolean
}

export interface EnrollmentSummary {
  course_id: number
  course_code: string
  course_title: string
  category: string
  difficulty: string
  instructor_name: string
  progress_pct: number
  modules_completed: number
  modules_total: number
  current_grade: number
  status: string
}

export interface ConceptMasteryItem {
  concept_id: number
  concept_code: string
  concept_name: string
  course_code: string
  mastery_score: number
  confidence: number
  attempts_count: number
}

export interface RecommendationItem {
  resource_id: number
  title: string
  course_code: string
  course_title: string
  concept_id: number
  concept_name: string
  resource_type: string
  difficulty: string
  estimated_minutes: number
  summary: string
  content_body: string
  tags: string[]
  match_score: number
  current_concept_mastery: number
  prerequisite_status: string
  interaction_status: string
  rationale: string
}

export interface StudentDashboardPayload {
  profile: {
    id: number
    user_id: number
    full_name: string
    email: string
    avatar_initials: string
    student_code: string
    cohort: string
    program_track: string
    semester: number
    study_goal_hours_weekly: number
    attendance_rate: number
    engagement_index: number
    assignment_timeliness: number
    current_gpa: number
    avg_concept_mastery: number
  }
  ml_intelligence: {
    predicted_final_score: number
    risk_score: number
    risk_level: 'low' | 'moderate' | 'high'
    drivers: RiskDriver[]
    cluster: {
      cluster_id: number
      cluster_label: string
      cluster_description: string
      pca_x: number
      pca_y: number
    }
    features: Record<string, number>
  }
  trajectory: TrajectoryPoint[]
  enrollments: EnrollmentSummary[]
  concept_masteries: ConceptMasteryItem[]
  recent_submissions: Array<{
    submission_id: number
    assessment_id: number
    assessment_title: string
    score_pct: number
    passed: boolean
    time_spent_seconds: number
    submitted_at: string
  }>
  recommendations: RecommendationItem[]
  interventions: Array<{
    id: number
    intervention_type: string
    priority: string
    notes: string
    status: string
    created_at: string
  }>
}

export interface CourseItem {
  id: number
  code: string
  title: string
  category: string
  difficulty: string
  credit_hours: number
  instructor_name: string
  description: string
  modules_count: number
  concepts_count: number
  resources_count: number
  enrolled_count: number
  cohort_avg_grade: number
  student_progress: number | null
  student_grade: number | null
  student_status: string | null
}

export interface AssessmentSummary {
  id: number
  course_id: number
  course_code: string
  course_title: string
  title: string
  assessment_type: string
  description: string
  duration_minutes: number
  passing_score: number
  total_points: number
  questions_count: number
  is_published: boolean
  cohort_submissions_count: number
  cohort_mean_score: number
  latest_submission: {
    submission_id: number
    score_pct: number
    passed: boolean
    submitted_at: string
  } | null
}

export interface AssistantCitation {
  title: string
  course_code: string
  kind: string
  relevance: number
}

export interface AssistantAction {
  label: string
  route: string
}

export interface AssistantChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  citations: AssistantCitation[]
  suggested_actions: AssistantAction[]
  created_at: string
}

export interface CohortAnalyticsPayload {
  kpis: {
    total_students: number
    high_risk_count: number
    moderate_risk_count: number
    low_risk_count: number
    avg_predicted_score: number
    avg_attendance_rate: number
    avg_engagement_index: number
    avg_gpa: number
    open_interventions: number
    total_submissions: number
  }
  risk_distribution: Array<{ tier: string; count: number; key: string }>
  cohort_comparison: Array<{
    cohort: string
    short_name: string
    student_count: number
    avg_predicted_score: number
    avg_attendance: number
    avg_engagement: number
    high_risk_count: number
  }>
  weekly_trends: Array<{
    week_label: string
    avg_quiz_score: number
    avg_study_hours: number
    avg_attendance: number
  }>
  concept_analytics: Array<{
    concept_id: number
    code: string
    name: string
    course_code: string
    mean_mastery: number
    below_threshold_pct: number
    difficulty_weight: number
  }>
  cluster_scatter: Array<{
    student_id: number
    student_code: string
    full_name: string
    cluster_id: number
    cluster_label: string
    pca_x: number
    pca_y: number
    predicted_score: number
    risk_level: string
  }>
  score_distribution: Array<{ range: string; count: number }>
  priority_students: Array<{
    id: number
    student_code: string
    full_name: string
    email: string
    cohort: string
    cluster_label: string
    attendance_rate: number
    engagement_index: number
    predicted_final_score: number
    risk_score: number
    risk_level: 'low' | 'moderate' | 'high'
  }>
}

export interface MLMetricsPayload {
  trained_at: string
  cohort_size: number
  risk_model: {
    sample_size: number
    positive_risk_count: number
    cv_folds: number
    selected_classifier: string
    classifier_metrics: {
      model: string
      accuracy: number
      precision: number
      recall: number
      f1_score: number
      roc_auc: number
    }
    classifier_comparison: Array<{
      model: string
      accuracy: number
      precision: number
      recall: number
      f1_score: number
      roc_auc: number
    }>
    confusion_matrix: {
      labels: string[]
      matrix: number[][]
    }
    selected_regressor: string
    regressor_metrics: {
      model: string
      mae: number
      rmse: number
      r2_score: number
    }
    regressor_comparison: Array<{
      model: string
      mae: number
      rmse: number
      r2_score: number
    }>
    feature_importances: Array<{
      feature: string
      label: string
      importance: number
      risk_correlation: number
    }>
  }
  clustering_model: {
    algorithm: string
    n_clusters: number
    silhouette_score: number
    calinski_harabasz_score: number
    pca_explained_variance_ratio: number[]
    clusters: Array<{
      cluster_id: number
      label: string
      description: string
      student_count: number
      centroid: Record<string, number>
    }>
  }
}
