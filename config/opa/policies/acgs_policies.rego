package acgs.policies

# Default deny policy
default allow = false

# Allow authenticated users to read their own data
allow {
    input.method == "GET"
    input.user.authenticated == true
    input.resource.owner == input.user.id
}

# Allow admins to perform any action
allow {
    input.user.role == "admin"
}

# Allow users to create new policies
allow {
    input.method == "POST"
    input.path == "/api/v1/policies"
    input.user.authenticated == true
}

# Rate limiting policy
rate_limit_exceeded {
    input.user.requests_per_minute > 100
}

# Security validation
security_check {
    not contains(input.data, "DROP TABLE")
    not contains(input.data, "<script>")
    not contains(input.data, "javascript:")
}
