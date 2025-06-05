package example.operational_rules.active

# This is a dummy operational rule, actively enforced.
# It could represent a specific constraint or permission.

default allow_action = false

# Allow action if the user is an admin and the resource is not critical.
allow_action {
    input.user.role == "admin"
    not is_critical_resource(input.resource.id)
    trace("Admin access granted to non-critical resource")
}

# Allow action if the user is an editor and action is "read" on a document.
allow_action {
    input.user.role == "editor"
    input.action == "read"
    input.resource.type == "document"
    trace("Editor read access granted to document")
}

# Helper function (could be part of a library or this rule set)
is_critical_resource(resource_id) {
    critical_resources := {"db_master", "auth_service_config"}
    critical_resources[resource_id]
}

# Example: Define a set of restricted actions
restricted_actions := {"delete_user", "format_disk"}

# Deny if the action is in the restricted set, regardless of user (unless overridden by higher priority)
deny_restricted_action[reason] {
    restricted_actions[input.action]
    reason := sprintf("Action '%s' is restricted.", [input.action])
    trace(reason) # For OPA trace
}

# This rule might be part of a larger policy set where `allow_action` and `deny_restricted_action`
# are combined by a higher-level policy decision point.
# For example:
# system_allow {
#   allow_action
#   not deny_restricted_action[_] # ensure no deny rule for this action fires
# }
#
# Or, if this file itself is the decision point for a specific scope:
# final_decision := {"allowed": allow_action, "denied_reasons": deny_restricted_action}
# This structure depends on how OPA is queried by the application.
# For this dummy rule, we assume `allow_action` and `deny_restricted_action` are queried separately or composed elsewhere.
