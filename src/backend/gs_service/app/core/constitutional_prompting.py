"""
Constitutional Prompting Module for ACGS-PGP Phase 1

This module implements constitutional prompting methodology that systematically
integrates AC principles as constitutional context in LLM prompts for policy synthesis.
Enhanced with WINA-informed constitutional principle updates for optimization.
"""

import logging
from typing import List, Dict, Any, Optional
from ..schemas import ACPrinciple
from ..services.ac_client import ac_service_client

# Import WINA constitutional integration
try:
    import logging
    from shared.wina.constitutional_integration import (
        WINAConstitutionalPrincipleAnalyzer,
        WINAConstitutionalUpdateService
    )
    WINA_AVAILABLE = True
except ImportError:
    WINA_AVAILABLE = False
    _logger = logging.getLogger(__name__)
    _logger.warning("WINA constitutional integration not available")

logger = logging.getLogger(__name__)


class ConstitutionalPromptBuilder:
    """
    Builds constitutional prompts that integrate AC principles as constitutional context
    for LLM-based policy synthesis. Enhanced with WINA-informed constitutional updates.
    """

    def __init__(self, enable_wina_integration: bool = True):
        """
        Initialize the Constitutional Prompt Builder.

        Args:
            enable_wina_integration: Whether to enable WINA constitutional integration
        """
        self.enable_wina_integration = enable_wina_integration and WINA_AVAILABLE

        # Initialize WINA services if available
        if self.enable_wina_integration:
            self.wina_analyzer = WINAConstitutionalPrincipleAnalyzer()
            self.wina_update_service = WINAConstitutionalUpdateService(analyzer=self.wina_analyzer)
            logger.info("WINA constitutional integration enabled")
        else:
            self.wina_analyzer = None
            self.wina_update_service = None
            logger.info("WINA constitutional integration disabled")

        self.constitutional_preamble = """
You are an AI Constitutional Interpreter for the ACGS-PGP (AI Compliance Governance System - Policy Generation Platform).
Your role is to synthesize governance policies that are constitutionally compliant with the established AC (Artificial Constitution) principles.

CONSTITUTIONAL FRAMEWORK:
The AC principles provided below form the constitutional foundation that MUST guide all policy synthesis.
Each principle has priority weights, scope definitions, and normative statements that constrain policy generation.

WINA OPTIMIZATION CONTEXT:
When WINA (Weight Informed Neuron Activation) optimization is enabled, constitutional principles may include
efficiency optimization constraints that balance performance gains with constitutional compliance.
These WINA-informed principles ensure that LLM optimization maintains constitutional integrity.

CONSTITUTIONAL COMPLIANCE REQUIREMENTS:
1. All generated policies MUST align with the constitutional principles
2. Higher priority principles take precedence in case of conflicts
3. Policies MUST respect the scope limitations of each principle
4. Generated rules MUST be traceable to their constitutional foundations
5. Constitutional fidelity is paramount - never violate core principles
"""

    async def build_constitutional_context(
        self, 
        context: str, 
        category: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build constitutional context by fetching relevant AC principles for the given context.
        
        Args:
            context: The target context for policy synthesis
            category: Optional category filter for principles
            auth_token: Authentication token for AC service
            
        Returns:
            Dictionary containing constitutional context information
        """
        try:
            # Fetch active principles for the given context
            # This would use the new enhanced AC service endpoints
            relevant_principles = await self._fetch_relevant_principles(context, category, auth_token)
            
            constitutional_context = {
                "context": context,
                "category": category,
                "principles": relevant_principles,
                "principle_count": len(relevant_principles),
                "constitutional_hierarchy": self._build_principle_hierarchy(relevant_principles),
                "scope_constraints": self._extract_scope_constraints(relevant_principles),
                "normative_framework": self._build_normative_framework(relevant_principles)
            }
            
            logger.info(f"Built constitutional context for '{context}' with {len(relevant_principles)} principles")
            return constitutional_context
            
        except Exception as e:
            logger.error(f"Failed to build constitutional context for '{context}': {e}")
            return {
                "context": context,
                "category": category,
                "principles": [],
                "principle_count": 0,
                "error": "An internal error occurred while building the constitutional context."
            }

    async def _fetch_relevant_principles(
        self,
        context: str,
        category: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch principles relevant to the given context and category."""
        try:
            # Use the enhanced AC service endpoints for context-specific principles
            relevant_principles_objs = await ac_service_client.get_principles_for_context(
                context=context,
                category=category,
                auth_token=auth_token
            )

            # Convert to dictionaries and sort by priority weight
            relevant_principles = [principle.model_dump() for principle in relevant_principles_objs]

            # Sort by priority weight (highest first)
            relevant_principles.sort(
                key=lambda p: p.get('priority_weight', 0.0),
                reverse=True
            )

            # If no context-specific principles found, fall back to category-based search
            if not relevant_principles and category:
                category_principles = await ac_service_client.get_principles_by_category(
                    category=category,
                    auth_token=auth_token
                )
                relevant_principles = [principle.model_dump() for principle in category_principles]
                relevant_principles.sort(
                    key=lambda p: p.get('priority_weight', 0.0),
                    reverse=True
                )

            # If still no principles, try keyword-based search
            if not relevant_principles:
                context_keywords = context.lower().split()
                keyword_principles = await ac_service_client.search_principles_by_keywords(
                    keywords=context_keywords,
                    auth_token=auth_token
                )
                relevant_principles = [principle.model_dump() for principle in keyword_principles]
                relevant_principles.sort(
                    key=lambda p: p.get('priority_weight', 0.0),
                    reverse=True
                )

            return relevant_principles

        except Exception as e:
            logger.error(f"Failed to fetch relevant principles: {e}")
            # Fallback to the original method
            try:
                all_principles = await ac_service_client.list_principles(auth_token=auth_token)

                relevant_principles = []
                for principle in all_principles:
                    principle_dict = principle.model_dump()

                    # Check if principle applies to the context
                    if self._principle_applies_to_context(principle_dict, context):
                        # Check category filter if provided
                        if category is None or principle_dict.get('category') == category:
                            relevant_principles.append(principle_dict)

                # Sort by priority weight (highest first)
                relevant_principles.sort(
                    key=lambda p: p.get('priority_weight', 0.0),
                    reverse=True
                )

                return relevant_principles
            except Exception as fallback_error:
                logger.error(f"Fallback principle fetch also failed: {fallback_error}")
                return []

    def _principle_applies_to_context(self, principle: Dict[str, Any], context: str) -> bool:
        """Check if a principle applies to the given context."""
        scope = principle.get('scope', [])
        
        # If no scope defined, assume it applies to all contexts
        if not scope:
            return True
            
        # Check if context matches any scope item
        return context in scope or any(context.lower() in s.lower() for s in scope)

    def _build_principle_hierarchy(self, principles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build a hierarchical representation of principles based on priority weights."""
        hierarchy = []
        
        for principle in principles:
            priority_weight = principle.get('priority_weight', 0.0)
            
            # Categorize by priority level
            if priority_weight >= 0.8:
                priority_level = "CRITICAL"
            elif priority_weight >= 0.6:
                priority_level = "HIGH"
            elif priority_weight >= 0.4:
                priority_level = "MEDIUM"
            elif priority_weight >= 0.2:
                priority_level = "LOW"
            else:
                priority_level = "INFORMATIONAL"
            
            hierarchy.append({
                "id": principle.get('id'),
                "name": principle.get('name'),
                "priority_weight": priority_weight,
                "priority_level": priority_level,
                "category": principle.get('category'),
                "normative_statement": principle.get('normative_statement')
            })
        
        return hierarchy

    def _extract_scope_constraints(self, principles: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract scope constraints from principles."""
        constraints = {}
        
        for principle in principles:
            principle_id = str(principle.get('id'))
            scope = principle.get('scope', [])
            constraints[principle_id] = scope
        
        return constraints

    def _build_normative_framework(self, principles: List[Dict[str, Any]]) -> Dict[str, str]:
        """Build a normative framework from principle normative statements."""
        framework = {}
        
        for principle in principles:
            principle_id = str(principle.get('id'))
            normative_statement = principle.get('normative_statement')
            
            if normative_statement:
                framework[principle_id] = normative_statement
        
        return framework

    def build_constitutional_prompt(
        self, 
        constitutional_context: Dict[str, Any],
        synthesis_request: str,
        target_format: str = "datalog"
    ) -> str:
        """
        Build a constitutional prompt that integrates AC principles as constitutional context.
        
        Args:
            constitutional_context: Constitutional context built by build_constitutional_context
            synthesis_request: The specific synthesis request
            target_format: Target format for generated policies (datalog, rego, etc.)
            
        Returns:
            Complete constitutional prompt for LLM
        """
        principles = constitutional_context.get('principles', [])
        hierarchy = constitutional_context.get('constitutional_hierarchy', [])
        
        # Build the constitutional principles section
        constitutional_principles_section = self._build_principles_section(principles, hierarchy)
        
        # Build the synthesis instructions
        synthesis_instructions = self._build_synthesis_instructions(
            constitutional_context, synthesis_request, target_format
        )
        
        # Combine all sections
        full_prompt = f"""
{self.constitutional_preamble}

{constitutional_principles_section}

{synthesis_instructions}

SYNTHESIS REQUEST:
{synthesis_request}

TARGET FORMAT: {target_format.upper()}

CONSTITUTIONAL COMPLIANCE VERIFICATION:
Before providing your response, verify that:
1. All generated policies align with the constitutional principles above
2. Higher priority principles are given precedence
3. Scope constraints are respected
4. Generated rules are traceable to constitutional foundations
5. No constitutional violations exist in the output

Please provide your constitutionally compliant policy synthesis:
"""
        
        return full_prompt.strip()

    def _build_principles_section(
        self, 
        principles: List[Dict[str, Any]], 
        hierarchy: List[Dict[str, Any]]
    ) -> str:
        """Build the constitutional principles section of the prompt."""
        if not principles:
            return "CONSTITUTIONAL PRINCIPLES: None applicable to this context."
        
        section = "CONSTITUTIONAL PRINCIPLES (in priority order):\n\n"
        
        for i, principle in enumerate(principles, 1):
            priority_weight = principle.get('priority_weight', 0.0)
            priority_info = next((h for h in hierarchy if h['id'] == principle['id']), {})
            priority_level = priority_info.get('priority_level', 'UNSPECIFIED')
            
            section += f"{i}. PRINCIPLE {principle['id']}: {principle['name']}\n"
            section += f"   Priority: {priority_weight:.2f} ({priority_level})\n"
            section += f"   Category: {principle.get('category', 'Unspecified')}\n"
            section += f"   Content: {principle['content']}\n"
            
            if principle.get('normative_statement'):
                section += f"   Normative Statement: {principle['normative_statement']}\n"
            
            if principle.get('scope'):
                section += f"   Scope: {', '.join(principle['scope'])}\n"
            
            if principle.get('constraints'):
                section += f"   Constraints: {principle['constraints']}\n"
            
            section += "\n"
        
        return section

    def _build_synthesis_instructions(
        self, 
        constitutional_context: Dict[str, Any],
        synthesis_request: str,
        target_format: str
    ) -> str:
        """Build synthesis instructions based on constitutional context."""
        context = constitutional_context.get('context', 'general')
        principle_count = constitutional_context.get('principle_count', 0)
        
        instructions = f"""
SYNTHESIS INSTRUCTIONS:
Context: {context}
Applicable Principles: {principle_count}

You must synthesize governance policies that:
1. Are constitutionally compliant with ALL applicable principles above
2. Respect the priority hierarchy (higher priority principles override lower ones)
3. Stay within the scope constraints of each principle
4. Generate {target_format} rules that are enforceable and verifiable
5. Include constitutional traceability (which principles influenced each rule)

CONSTITUTIONAL CONFLICT RESOLUTION:
If principles conflict, resolve using this hierarchy:
1. Higher priority_weight principles take precedence
2. More specific scope constraints override general ones
3. Explicit normative statements guide interpretation
4. When in doubt, choose the most restrictive interpretation that satisfies all principles
"""
        
        return instructions

    async def build_wina_enhanced_constitutional_context(
        self,
        context: str,
        category: Optional[str] = None,
        auth_token: Optional[str] = None,
        optimization_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build WINA-enhanced constitutional context with optimization analysis.

        Args:
            context: The target context for policy synthesis
            category: Optional category filter for principles
            auth_token: Authentication token for AC service
            optimization_context: WINA optimization context

        Returns:
            Enhanced constitutional context with WINA analysis
        """
        # Build base constitutional context
        constitutional_context = await self.build_constitutional_context(context, category, auth_token)

        # Add WINA enhancements if available
        if self.enable_wina_integration and self.wina_analyzer:
            try:
                # Set default optimization context
                if not optimization_context:
                    optimization_context = {
                        "target_gflops_reduction": 0.5,
                        "min_accuracy_retention": 0.95,
                        "optimization_mode": "conservative",
                        "context": context
                    }

                # Analyze principles for WINA optimization
                wina_analysis_results = {}
                principles = constitutional_context.get('principles', [])

                for principle in principles:
                    try:
                        analysis = await self.wina_analyzer.analyze_principle_for_wina_optimization(
                            principle, optimization_context
                        )
                        wina_analysis_results[str(principle.get('id'))] = analysis

                    except Exception as e:
                        logger.error(f"WINA analysis failed for principle {principle.get('id')}: {e}")
                        wina_analysis_results[str(principle.get('id'))] = {
                            "error": str(e),
                            "optimization_potential": 0.0
                        }

                # Add WINA enhancements to constitutional context
                constitutional_context.update({
                    "wina_enabled": True,
                    "wina_analysis": wina_analysis_results,
                    "optimization_context": optimization_context,
                    "wina_summary": self._build_wina_summary(wina_analysis_results),
                    "optimization_recommendations": self._build_optimization_recommendations(wina_analysis_results)
                })

                logger.info(f"Enhanced constitutional context with WINA analysis for {len(principles)} principles")

            except Exception as e:
                logger.error(f"WINA enhancement failed: {e}")
                constitutional_context["wina_enabled"] = False
                constitutional_context["wina_error"] = str(e)
        else:
            constitutional_context["wina_enabled"] = False

        return constitutional_context

    def _build_wina_summary(self, wina_analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Build summary of WINA analysis results."""
        if not wina_analysis_results:
            return {"total_principles": 0, "optimization_potential": 0.0}

        total_principles = len(wina_analysis_results)
        high_potential = len([r for r in wina_analysis_results.values()
                             if r.get("optimization_potential", 0) > 0.7])
        medium_potential = len([r for r in wina_analysis_results.values()
                               if 0.4 <= r.get("optimization_potential", 0) <= 0.7])
        low_potential = len([r for r in wina_analysis_results.values()
                            if r.get("optimization_potential", 0) < 0.4])

        avg_potential = sum(r.get("optimization_potential", 0) for r in wina_analysis_results.values()) / total_principles

        return {
            "total_principles": total_principles,
            "high_potential_count": high_potential,
            "medium_potential_count": medium_potential,
            "low_potential_count": low_potential,
            "average_optimization_potential": avg_potential,
            "optimization_feasible": avg_potential > 0.3
        }

    def _build_optimization_recommendations(self, wina_analysis_results: Dict[str, Any]) -> List[str]:
        """Build optimization recommendations based on WINA analysis."""
        recommendations = []

        if not wina_analysis_results:
            return ["No WINA analysis available"]

        high_potential_principles = [
            principle_id for principle_id, analysis in wina_analysis_results.items()
            if analysis.get("optimization_potential", 0) > 0.7
        ]

        if high_potential_principles:
            recommendations.append(f"Consider aggressive WINA optimization for principles: {', '.join(high_potential_principles)}")

        safety_critical_principles = [
            principle_id for principle_id, analysis in wina_analysis_results.items()
            if "safety_critical_principle" in analysis.get("risk_factors", [])
        ]

        if safety_critical_principles:
            recommendations.append(f"Implement additional safety monitoring for: {', '.join(safety_critical_principles)}")

        recommendations.append("Monitor constitutional compliance continuously during optimization")
        recommendations.append("Implement fallback mechanisms for optimization failures")

        return recommendations

    def build_wina_enhanced_constitutional_prompt(
        self,
        constitutional_context: Dict[str, Any],
        synthesis_request: str,
        target_format: str = "datalog"
    ) -> str:
        """
        Build WINA-enhanced constitutional prompt with optimization context.

        Args:
            constitutional_context: WINA-enhanced constitutional context
            synthesis_request: The specific synthesis request
            target_format: Target format for generated policies

        Returns:
            WINA-enhanced constitutional prompt for LLM
        """
        # Build base prompt
        base_prompt = self.build_constitutional_prompt(constitutional_context, synthesis_request, target_format)

        # Add WINA enhancements if available
        if constitutional_context.get("wina_enabled", False):
            wina_section = self._build_wina_optimization_section(constitutional_context)

            # Insert WINA section before synthesis instructions
            prompt_parts = base_prompt.split("SYNTHESIS INSTRUCTIONS:")
            if len(prompt_parts) == 2:
                enhanced_prompt = f"{prompt_parts[0]}\n{wina_section}\n\nSYNTHESIS INSTRUCTIONS:{prompt_parts[1]}"
            else:
                enhanced_prompt = f"{base_prompt}\n\n{wina_section}"
        else:
            enhanced_prompt = base_prompt

        return enhanced_prompt

    def _build_wina_optimization_section(self, constitutional_context: Dict[str, Any]) -> str:
        """Build WINA optimization section for constitutional prompt."""
        wina_summary = constitutional_context.get("wina_summary", {})
        optimization_recommendations = constitutional_context.get("optimization_recommendations", [])
        optimization_context = constitutional_context.get("optimization_context", {})

        avg_potential = wina_summary.get('average_optimization_potential', 0.0)
        section = f"""
WINA OPTIMIZATION CONTEXT:
Optimization Mode: {optimization_context.get('optimization_mode', 'conservative')}
Target GFLOPs Reduction: {optimization_context.get('target_gflops_reduction', 0.5)}
Minimum Accuracy Retention: {optimization_context.get('min_accuracy_retention', 0.95)}

OPTIMIZATION ANALYSIS SUMMARY:
- Total Principles Analyzed: {wina_summary.get('total_principles', 0)}
- High Optimization Potential: {wina_summary.get('high_potential_count', 0)}
- Medium Optimization Potential: {wina_summary.get('medium_potential_count', 0)}
- Low Optimization Potential: {wina_summary.get('low_potential_count', 0)}
- Average Optimization Potential: {avg_potential:.3f}
- Optimization Feasible: {wina_summary.get('optimization_feasible', False)}

OPTIMIZATION RECOMMENDATIONS:
"""

        for i, recommendation in enumerate(optimization_recommendations, 1):
            section += f"{i}. {recommendation}\n"

        section += """
WINA CONSTITUTIONAL CONSTRAINTS:
When generating policies, ensure that:
1. WINA optimization constraints are included where applicable
2. Efficiency gains do not compromise constitutional compliance
3. Fallback mechanisms are specified for optimization failures
4. Performance monitoring requirements are included
5. Constitutional fidelity is maintained during optimization
"""

        return section


# Global instance for use across the GS service
constitutional_prompt_builder = ConstitutionalPromptBuilder()
