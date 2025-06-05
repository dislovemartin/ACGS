"""
Datalog Rule Templates

This module contains predefined Datalog rule templates as Python strings.
These templates have placeholders that can be filled by the LLM's output
or other contextual information during the rule generation process.

Placeholders are typically denoted by surrounding them with double curly braces,
e.g., {{ENTITY}}, {{ACTION}}, {{RESOURCE}}, {{ATTRIBUTE}}, {{ROLE}}, {{PRINCIPLE_ID}}.
"""

# Template for asserting a user has a specific role based on an attribute
USER_ROLE_ASSERTION = """\
user_role_is({{USER_VAR}}, {{ROLE_VALUE}}) :- 
    has_attribute({{USER_VAR}}, '{{ROLE_ATTRIBUTE}}', {{ROLE_VALUE}}),
    principle_source({{PRINCIPLE_ID}})."""

# Template for allowing an action if a user has a specific role
ROLE_BASED_ACTION_ALLOW = """\
can_perform({{USER_VAR}}, {{ACTION_VALUE}}, {{RESOURCE_VAR}}) :- 
    user_role_is({{USER_VAR}}, {{ROLE_VALUE}}),
    principle_source({{PRINCIPLE_ID}})."""

# Template for allowing an action if a user has a specific role AND a resource has a specific property
ROLE_RESOURCE_PROPERTY_ACTION_ALLOW = """\
can_perform({{USER_VAR}}, {{ACTION_VALUE}}, {{RESOURCE_VAR}}) :- 
    user_role_is({{USER_VAR}}, {{ROLE_VALUE}}),
    resource_has_property({{RESOURCE_VAR}}, '{{PROPERTY_NAME}}', {{PROPERTY_VALUE}}),
    principle_source({{PRINCIPLE_ID}})."""

# Template for denying an action if a resource is sensitive and user lacks a specific role
SENSITIVE_DATA_DENY = """\
cannot_perform({{USER_VAR}}, {{ACTION_VALUE}}, {{RESOURCE_VAR}}) :-
    is_sensitive({{RESOURCE_VAR}}),
    NOT user_role_is({{USER_VAR}}, '{{REQUIRED_ROLE_FOR_SENSITIVE}}'),
    principle_source({{PRINCIPLE_ID}})."""
    
# Generic template for logging an event based on an action being performed
LOG_ACTION_EVENT = """\
log_event('{{ACTION_VALUE}}', {{USER_VAR}}, {{RESOURCE_VAR}}, '{{TIMESTAMP_VAR}}') :-
    performed_action({{USER_VAR}}, {{ACTION_VALUE}}, {{RESOURCE_VAR}}, {{TIMESTAMP_VAR}}),
    principle_source({{PRINCIPLE_ID}})."""

# A very generic template based on LLM's suggested structure
GENERIC_LLM_SUGGESTED_RULE = """\
{{LLM_SUGGESTED_STRUCTURE}} :- principle_source({{PRINCIPLE_ID}}).
# Note: This template assumes LLM_SUGGESTED_STRUCTURE is a valid Datalog head and body.
# Further parsing and validation might be needed for the LLM output.
"""

# Simple fact asserting the source of a rule
PRINCIPLE_SOURCE_FACT = """\
principle_source({{PRINCIPLE_ID}})."""


# Example of how these might be used (for illustration, not functional code here)
# template_filler = {
#     "USER_VAR": "User",
#     "ROLE_VALUE": "'admin'",
#     "ROLE_ATTRIBUTE": "userRole",
#     "ACTION_VALUE": "'read'",
#     "RESOURCE_VAR": "Resource",
#     "PROPERTY_NAME": "sensitivity",
#     "PROPERTY_VALUE": "'high'",
#     "REQUIRED_ROLE_FOR_SENSITIVE": "'auditor'",
#     "TIMESTAMP_VAR": "Timestamp",
#     "PRINCIPLE_ID": "p123",
#     "LLM_SUGGESTED_STRUCTURE": "access_granted(X, Y) :- user(X), resource(Y), department(X, 'research')"
# }

# filled_template = USER_ROLE_ASSERTION.format(**template_filler)
# print(filled_template)
# filled_generic = GENERIC_LLM_SUGGESTED_RULE.format(**template_filler)
# print(filled_generic)
