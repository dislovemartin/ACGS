from pyDatalog import pyDatalog

class DatalogEngine:
    def __init__(self):
        self.clear_rules_and_facts()

    def clear_rules_and_facts(self):
        """Clears all rules and facts from the pyDatalog engine."""
        pyDatalog.clear()

    def load_rules(self, rules: list[str]):
        """
        Loads a list of Datalog rules (as strings) into the engine.
        Each rule string should be a valid pyDatalog rule.
        Example: "can_access(User, Resource) <= user_role(User, 'admin')"
        """
        for rule_str in rules:
            try:
                # pyDatalog's logic_program expects clauses to be asserted directly
                # This can be done by exec-ing them in the pyDatalog context or using .load()
                # For simplicity and directness with string rules:
                pyDatalog.load(rule_str)
            except Exception as e:
                print(f"Error loading Datalog rule: '{rule_str}'. Error: {e}")
                # Depending on strictness, you might want to raise the error or log and continue

    def add_facts(self, facts: list[str]):
        """
        Adds a list of Datalog facts (as strings) into the engine.
        Each fact string should be a valid pyDatalog fact.
        Example: "+user_role('alice', 'editor')"
        Facts must start with '+' to be added.
        """
        for fact_str in facts:
            if not fact_str.strip().startswith("+"):
                fact_str = "+" + fact_str.strip() # Ensure it's an assertion
            try:
                pyDatalog.load(fact_str)
            except Exception as e:
                print(f"Error loading Datalog fact: '{fact_str}'. Error: {e}")

    def query(self, query_string: str) -> list:
        """
        Executes a Datalog query and returns the results.
        query_string: e.g., "can_access('alice', 'document123')"
        Returns a list of tuples, where each tuple is a result.
        If the query is for a predicate with no variables (a ground query),
        it will return [()] if true, or [] if false.
        """
        try:
            # For pyDatalog, queries are typically done by asking for the value of a predicate.
            # Example: pyDatalog.ask("can_access('alice',X)") returns a Query object or None
            # The Query object itself can be iterated or converted to a list of tuples.
            result = pyDatalog.ask(query_string)
            if result is not None:
                return list(result.answers) # result.answers gives list of tuples
            return [] # No results or predicate not defined
        except Exception as e:
            print(f"Error executing Datalog query: '{query_string}'. Error: {e}")
            return []

    def build_facts_from_context(self, context: dict) -> list[str]:
        """
        Transforms a context dictionary into a list of Datalog fact strings.
        Example context:
        {
            "user": {"id": "alice", "role": "editor", "department": "research"},
            "resource": {"id": "doc123", "type": "report", "sensitivity": "high"},
            "action": {"type": "read"}
        }
        Generates facts like:
        +user_attribute('alice', 'role', 'editor')
        +resource_attribute('doc123', 'type', 'report')
        +action_type('read')
        """
        facts = []
        for entity_type, attributes in context.items():
            if isinstance(attributes, dict): # user, resource, action, environment
                entity_id = attributes.get("id") # Optional, action might not have an ID
                for key, value in attributes.items():
                    if key == "id": # ID is often used to link attributes, not as an attribute itself in this model
                        if entity_type != "action": # Action attributes are often direct, e.g. action_type('read')
                             facts.append(f"+{entity_type}_id('{value}')") # e.g. +user_id('alice')
                    else:
                        if entity_id and entity_type != "action": # e.g. user_attribute('alice', 'role', 'editor')
                            facts.append(f"+{entity_type}_attribute('{entity_id}', '{key}', '{str(value)}')" )
                        else: # For action or entities without explicit ID in this part of context
                            facts.append(f"+{entity_type}_{key}('{str(value)}')" ) # e.g. +action_type('read')
            else: # Direct context values
                 facts.append(f"+context_value('{entity_type}', '{str(attributes)}')")
        return facts

# Global instance
datalog_engine = DatalogEngine()

# Example Usage (for testing this file)
if __name__ == "__main__":
    engine = DatalogEngine()
    
    # Load rules
    rules_to_load = [
        "can_read(User, Document) <= user_role(User, 'editor') & document_type(Document, 'report')",
        "can_read(User, Document) <= user_role(User, 'admin')",
        "user_role(User, Role) <= user_attribute(User, 'role', Role)" # More generic rule
    ]
    engine.load_rules(rules_to_load)
    print("Rules loaded.")

    # Add facts from context
    query_context = {
        "user": {"id": "alice", "role": "editor"},
        "resource": {"id": "report123", "type": "report"},
        "action": {"type": "read"}
    }
    context_facts = engine.build_facts_from_context(query_context)
    # Manually add facts based on context for this test, as build_facts_from_context is generic
    facts_to_add = [
        # "+user_role('alice', 'editor')", # This would be generated by a rule if user_attribute is used
        "+user_attribute('alice', 'role', 'editor')",
        "+document_type('report123', 'report')"
    ]
    engine.add_facts(facts_to_add)
    print(f"Facts added: {facts_to_add}")

    # Query
    print("\nQuerying: can_read('alice', 'report123')")
    result1 = engine.query("can_read('alice', 'report123')")
    print(f"Result: {result1} (Expected: [()] if true, indicating alice can read report123)")
    assert result1 == [()]


    engine.clear_rules_and_facts()
    engine.load_rules([
        "access_allowed(User, Action, Resource) <= user_has_role(User, Role) & permission_for_role(Role, Action, Resource)",
        "user_has_role(User, Role) <= user_attribute(User, 'roles', Role)" # Assuming 'roles' can be a list
    ])
    # pyDatalog handles list attributes by iterating if used in a specific way,
    # but direct string conversion might be tricky. Simpler to have one fact per role.
    # For this test, let's assume roles are individual facts or attributes.
    
    # A more pyDatalog-idiomatic way for multi-valued attributes like roles:
    # +user_attribute('bob', 'role', 'viewer')
    # +user_attribute('bob', 'role', 'commenter')
    # Then user_has_role(User, Role) <= user_attribute(User, 'role', Role) works directly.

    engine.add_facts([
        "+user_attribute('bob', 'roles', 'viewer')", # This might not work as expected with the rule above
                                                    # Let's use individual role facts for clarity
        "+user_attribute('bob', 'role', 'viewer')",
        "+permission_for_role('viewer', 'view', 'public_doc')"
    ])
    
    print("\nQuerying: access_allowed('bob', 'view', 'public_doc')")
    result2 = engine.query("access_allowed('bob', 'view', 'public_doc')")
    print(f"Result: {result2} (Expected: [()] if true)")
    assert result2 == [()]

    print("\nQuerying: access_allowed('bob', 'edit', 'public_doc')")
    result3 = engine.query("access_allowed('bob', 'edit', 'public_doc')")
    print(f"Result: {result3} (Expected: [] if false)")
    assert result3 == []
    
    print("\nAll Datalog engine tests passed (basic).")
