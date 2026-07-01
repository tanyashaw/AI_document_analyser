from langgraph.graph import StateGraph, END

from app.graph.state import RFPState

from app.agents.classifier_agent import classifier_agent
from app.agents.scope_agent import scope_agent
from app.agents.deadline_agent import deadline_agent
from app.agents.staffing_agent import staffing_agent
from app.agents.compliance_agent import compliance_agent
from app.agents.deliverables_agent import deliverables_agent
from app.agents.technical_agent import technical_agent
from app.agents.commercial_agent import commercial_agent
from app.agents.risks_agent import risks_agent
from app.agents.summary_agent import summary_agent


workflow = StateGraph(RFPState)

workflow.add_node("classifier_agent", classifier_agent)
workflow.add_node("scope_agent", scope_agent)
workflow.add_node("deadline_agent", deadline_agent)
workflow.add_node("staffing_agent", staffing_agent)
workflow.add_node("compliance_agent", compliance_agent)
workflow.add_node("deliverables_agent", deliverables_agent)
workflow.add_node("technical_agent", technical_agent)
workflow.add_node("commercial_agent", commercial_agent)
workflow.add_node("risks_agent", risks_agent)
# summary_agent runs last so it can see everything already extracted
workflow.add_node("summary_agent", summary_agent)

# Define sequential flow
workflow.set_entry_point("classifier_agent")
workflow.add_edge("classifier_agent", "scope_agent")
workflow.add_edge("scope_agent", "deadline_agent")
workflow.add_edge("deadline_agent", "staffing_agent")
workflow.add_edge("staffing_agent", "compliance_agent")
workflow.add_edge("compliance_agent", "deliverables_agent")
workflow.add_edge("deliverables_agent", "technical_agent")
workflow.add_edge("technical_agent", "commercial_agent")
workflow.add_edge("commercial_agent", "risks_agent")
workflow.add_edge("risks_agent", "summary_agent")
workflow.add_edge("summary_agent", END)

# Compile graph
app_graph = workflow.compile()