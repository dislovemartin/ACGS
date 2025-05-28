# Core Data Models

This document provides an overview of the core data models used within the ACGS-PGP system. These models are primarily defined as SQLAlchemy classes in `shared/models.py`. Understanding these models is crucial for developing and maintaining the system.

## User

-   **Description:** Represents a user of the system. It stores authentication credentials, user profile information, and role assignments.
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `username: String` (Unique username for login)
    -   `hashed_password: String` (Hashed password for security)
    -   `email: String` (Unique email address)
    -   `full_name: String` (Optional full name of the user)
    -   `role: String` (e.g., "system_admin", "user", "policy_auditor")
    -   `is_active: Boolean` (Indicates if the user account is active)
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
-   **Relationships:**
    -   `refresh_tokens`: One-to-many with `RefreshToken`.
    -   `created_principles`: One-to-many with `Principle` (user who created a principle).
    -   `created_policy_templates`: One-to-many with `PolicyTemplate`.
    -   `created_policies`: One-to-many with `Policy`.
    -   `audit_logs_as_actor`: One-to-many with `AuditLog` (user who performed an action).
-   **Primary Service:** `auth_service` is primarily responsible for managing `User` entities.

## RefreshToken

-   **Description:** Stores refresh tokens associated with users for maintaining sessions and re-authenticating without requiring credentials repeatedly.
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `user_id: Integer` (Foreign Key to `User`)
    -   `jti: String` (JWT ID, unique identifier for the token)
    -   `token: String` (The actual refresh token string, recommended to be hashed)
    -   `expires_at: DateTime` (Expiration date and time of the token)
    -   `created_at: DateTime`
    -   `is_revoked: Boolean` (Indicates if the token has been revoked)
-   **Relationships:**
    -   `user`: Many-to-one with `User`.
-   **Primary Service:** `auth_service`.

## Principle

-   **Description:** Represents a high-level constitutional principle or fundamental tenet within the AI governance framework. These are foundational elements upon which policies are built and evaluated. Corresponds to concepts like "Constitutional Principles" or "AC Principles".
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `name: String` (Unique name for the principle)
    -   `description: Text` (Detailed description of the principle)
    -   `content: Text` (The actual constitutional text or detailed definition)
    -   `version: Integer`
    -   `status: String` (e.g., "draft", "active", "archived")
    -   `priority_weight: Float` (For prioritization)
    -   `scope: JSONB` (Contexts where the principle applies)
    -   `normative_statement: Text`
    -   `constraints: JSONB` (Formal constraints)
    -   `rationale: Text`
    -   `keywords: JSONB`
    -   `category: String` (e.g., "Safety", "Privacy")
    -   `validation_criteria_nl: Text` (Natural language validation criteria)
    -   `constitutional_metadata: JSONB`
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
    -   `created_by_user_id: Integer` (Foreign Key to `User`)
-   **Relationships:**
    -   `created_by_user`: Many-to-one with `User`.
    -   Linked from `PolicyRule` (`source_principle_ids`) and `Policy` (`source_principle_ids`).
    -   `ac_amendments`: One-to-many with `ACAmendment`.
-   **Primary Service:** `ac_service` (Audit & Compliance) is likely the primary manager, though `gs_service` (Governance Structure/Synthesizer) might also interact heavily.

## PolicyRule

-   **Description:** Represents a specific, often machine-interpretable rule, such as a Datalog rule. These rules are the concrete implementation of policies and are used by the enforcement engine.
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `rule_name: String` (Optional human-readable name)
    -   `datalog_content: Text` (The Datalog rule content, unique per version)
    -   `version: Integer`
    -   `policy_id: Integer` (Foreign Key to `Policy`, if part of a larger policy)
    -   `source_principle_ids: JSONB` (IDs of `Principle`s this rule is derived from)
    -   `status: String` (e.g., "pending_synthesis", "verified_passed", "active")
    -   `verification_status: String` (e.g., "not_verified", "passed", "failed")
    -   `verified_at: DateTime`
    -   `verification_feedback: JSONB` (Details from formal verification)
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
    -   `synthesized_by_gs_run_id: String`
    -   `verified_by_fv_run_id: String`
-   **Relationships:**
    -   `policy`: Many-to-one with `Policy`.
-   **Primary Service:** `pgc_service` (Policy Governance & Compliance) for evaluation, `gs_service` for synthesis, `fv_service` for verification, and `integrity_service` for storage.

## AuditLog

-   **Description:** Records significant events and actions that occur within the system for auditing, security, and compliance purposes. Corresponds to "AuditLogEntry".
-   **Key Fields:**
    -   `id: UUID` (Primary Key, using UUID for global uniqueness)
    -   `timestamp: DateTime` (When the event occurred)
    -   `service_name: String` (Name of the service that generated the log, e.g., "auth_service")
    -   `event_type: String` (Type of event, e.g., "USER_LOGIN", "POLICY_RULE_CREATED")
    -   `actor_id: Integer` (Foreign Key to `User`, who performed the action)
    -   `entity_type: String` (Type of entity acted upon, e.g., "Principle", "Policy")
    -   `entity_id_int: Integer` / `entity_id_uuid: UUID` / `entity_id_str: String` (ID of the entity)
    -   `description: Text` (Human-readable summary of the event)
    -   `details: JSONB` (Structured details of the event, e.g., changes made)
-   **Relationships:**
    -   `actor`: Many-to-one with `User`.
-   **Primary Service:** `integrity_service` is the central collector and manager of audit logs from all services.

## PolicyTemplate

-   **Description:** Defines a reusable template for creating policies. Templates can include placeholders that are filled in to generate specific policy instances.
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `name: String` (Unique name for the template)
    -   `description: Text`
    -   `template_content: Text` (e.g., Datalog with placeholders)
    -   `parameters_schema: JSONB` (JSON schema for customizable parameters)
    -   `version: Integer`
    -   `status: String` (e.g., "draft", "active", "deprecated")
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
    -   `created_by_user_id: Integer` (Foreign Key to `User`)
-   **Relationships:**
    -   `created_by_user`: Many-to-one with `User`.
    -   `generated_policies`: One-to-many with `Policy`.
-   **Primary Service:** `gs_service` (Governance Structure/Synthesizer) is likely the primary manager.

## Policy

-   **Description:** Represents a high-level policy object, which might be composed of multiple `PolicyRule`s or instantiated from a `PolicyTemplate`. It defines the intent and scope of a specific governance policy.
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `name: String` (Unique name for the policy)
    -   `description: Text`
    -   `high_level_content: Text` (Natural language description or high-level definition)
    -   `version: Integer`
    -   `status: String` (e.g., "draft", "active", "archived")
    -   `template_id: Integer` (Foreign Key to `PolicyTemplate`, if instantiated from one)
    -   `customization_parameters: JSONB` (Parameters used if from a template)
    -   `source_principle_ids: JSONB` (IDs of `Principle`s this policy relates to)
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
    -   `created_by_user_id: Integer` (Foreign Key to `User`)
-   **Relationships:**
    -   `created_by_user`: Many-to-one with `User`.
    -   `template`: Many-to-one with `PolicyTemplate`.
    -   `rules`: One-to-many with `PolicyRule` (the actual rules implementing this policy).
-   **Primary Service:** `gs_service` for creation and management, `pgc_service` for enforcement (via `PolicyRule`s).

## ACMetaRule

-   **Description:** Represents meta-rules for the Artificial Constitution (AC), defining how the constitution itself can be governed, amended, or interpreted. Corresponds to "Constitutional Rules".
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `rule_type: String` (e.g., "amendment_procedure", "voting_threshold")
    -   `name: String`
    -   `description: Text`
    -   `rule_definition: JSONB` (Structured definition of the meta-rule)
    -   `threshold: String` (e.g., "0.67", "simple_majority")
    -   `stakeholder_roles: JSONB`
    -   `decision_mechanism: String`
    -   `status: String` (e.g., "active", "proposed")
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
    -   `created_by_user_id: Integer` (Foreign Key to `User`)
-   **Relationships:**
    -   `created_by_user`: Many-to-one with `User`.
-   **Primary Service:** Likely managed by a combination of `ac_service` and potentially `gs_service` or a dedicated constitutional council interface.

## ACAmendment

-   **Description:** Represents a proposal to amend a `Principle` (constitutional principle). It includes details of the proposed changes, justification, and tracks the amendment's lifecycle through review, voting, and implementation. Corresponds to "ACEnhancementProposal".
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `principle_id: Integer` (Foreign Key to `Principle` being amended)
    -   `amendment_type: String` (e.g., "modify", "add", "remove")
    -   `proposed_changes: Text`
    -   `justification: Text`
    -   `proposed_content: Text` (New content for the principle)
    -   `proposed_status: String` (New status for the principle)
    -   `status: String` (e.g., "proposed", "under_review", "approved")
    -   `voting_started_at: DateTime`
    -   `voting_ends_at: DateTime`
    -   `votes_for: Integer`
    -   `votes_against: Integer`
    -   `votes_abstain: Integer`
    -   `required_threshold: String`
    -   `consultation_period_days: Integer`
    -   `public_comment_enabled: Boolean`
    -   `stakeholder_groups: JSONB`
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
    -   `proposed_by_user_id: Integer` (Foreign Key to `User`)
-   **Relationships:**
    -   `principle`: Many-to-one with `Principle`.
    -   `proposed_by_user`: Many-to-one with `User`.
    -   `votes`: One-to-many with `ACAmendmentVote`.
    -   `comments`: One-to-many with `ACAmendmentComment`.
-   **Primary Service:** `ac_service` or a dedicated constitutional governance module.

## ACAmendmentVote

-   **Description:** Records an individual vote cast by a user (likely a "Constitutional Council member") on an `ACAmendment`.
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `amendment_id: Integer` (Foreign Key to `ACAmendment`)
    -   `voter_id: Integer` (Foreign Key to `User`)
    -   `vote: String` (e.g., "for", "against", "abstain")
    -   `reasoning: Text` (Optional explanation of the vote)
    -   `voted_at: DateTime`
-   **Relationships:**
    -   `amendment`: Many-to-one with `ACAmendment`.
    -   `voter`: Many-to-one with `User`.
-   **Primary Service:** `ac_service` or a dedicated constitutional governance module.

## ACAmendmentComment

-   **Description:** Stores public or stakeholder comments and feedback related to an `ACAmendment`. Corresponds to "ACEnhancementFeedback".
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `amendment_id: Integer` (Foreign Key to `ACAmendment`)
    -   `commenter_id: Integer` (Foreign Key to `User`, nullable for anonymous)
    -   `commenter_name: String` (For anonymous commenters)
    -   `commenter_email: String` (For anonymous commenters)
    -   `stakeholder_group: String`
    -   `comment_text: Text`
    -   `sentiment: String` (e.g., "support", "oppose", "neutral")
    -   `is_public: Boolean`
    -   `is_moderated: Boolean`
    -   `created_at: DateTime`
-   **Relationships:**
    -   `amendment`: Many-to-one with `ACAmendment`.
    -   `commenter`: Many-to-one with `User`.
-   **Primary Service:** `ac_service` or a dedicated constitutional governance module.

## ACConflictResolution

-   **Description:** Defines mappings and strategies for resolving conflicts that may arise between different `Principle`s or their practical application. This is a key part of the "M" (Mapping) component in the AC=⟨P,R,M,V⟩ framework.
-   **Key Fields:**
    -   `id: Integer` (Primary Key)
    -   `conflict_type: String` (e.g., "principle_contradiction")
    -   `principle_ids: JSONB` (List of `Principle` IDs involved)
    -   `context: String` (e.g., "data_retention_vs_privacy")
    -   `conflict_description: Text`
    -   `severity: String` (e.g., "low", "medium", "high")
    -   `resolution_strategy: String` (e.g., "principle_priority_based")
    -   `resolution_details: JSONB`
    -   `precedence_order: JSONB` (Priority order of principles for this context)
    -   `status: String` (e.g., "identified", "resolved")
    -   `resolved_at: DateTime`
    -   `created_at: DateTime`
    -   `updated_at: DateTime`
    -   `identified_by_user_id: Integer` (Foreign Key to `User`)
-   **Relationships:**
    -   `identified_by_user`: Many-to-one with `User`.
-   **Primary Service:** `ac_service` or a dedicated constitutional governance module.

---
*Note: Models like `Guideline`, `OperationalPolicy`, `ACGuideline`, and `ACEnhancementImplementation` were mentioned in the initial request but are not currently defined in `shared/models.py`. If these are added later, this document should be updated.*
