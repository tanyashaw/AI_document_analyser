from concurrent.futures import ThreadPoolExecutor, as_completed
import copy

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


# The 8 extraction agents are independent — they all read text and write
# to distinct state keys, so they can safely run in parallel.
_PARALLEL_AGENTS = [
    ("scope", scope_agent),
    ("deadlines", deadline_agent),
    ("staffing", staffing_agent),
    ("compliance", compliance_agent),
    ("deliverables", deliverables_agent),
    ("technical", technical_agent),
    ("commercial", commercial_agent),
    ("risks", risks_agent),
]


def _run_agent_isolated(agent_fn, state: dict) -> dict:
    """Run a single agent on a copy of state and return only its output keys."""
    result = agent_fn(copy.deepcopy(state))
    return result


class _ParallelWorkflow:
    """
    Drop-in replacement for the compiled LangGraph app_graph.
    Exposes the same .invoke(state) interface.

    Execution order:
      1. classifier_agent   (sequential — sets document_type)
      2. 8 extraction agents (parallel — each reads text, writes to own key)
      3. summary_agent      (sequential — reads all extraction outputs)
    """

    def invoke(self, state: dict) -> dict:
        # Step 1: classify the document
        state = classifier_agent(state)

        # Step 2: run all extraction agents in parallel
        # max_workers=3 to avoid bursting Gemini's free-tier rate limits (15 RPM)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_run_agent_isolated, agent_fn, state): key
                for key, agent_fn in _PARALLEL_AGENTS
            }
            for future in as_completed(futures):
                result = future.result()
                # Merge only the keys each agent owns back into shared state
                state.update(result)

        # Step 3: summarise using everything extracted above
        state = summary_agent(state)

        return state


# Public name — imported by rfp.py as `app_graph`
app_graph = _ParallelWorkflow()