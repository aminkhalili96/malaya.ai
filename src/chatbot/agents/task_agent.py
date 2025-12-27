"""
Task Agent for multi-step task execution using LangGraph.
Chains multiple tools together to complete complex requests.
"""
from typing import TypedDict, Annotated, Sequence, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

class AgentState(TypedDict):
    """State for the task agent."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    current_step: int
    total_steps: int
    steps_completed: List[dict]
    final_result: Optional[str]

class TaskAgent:
    """
    Multi-step task execution agent.
    
    Example usage:
        agent = TaskAgent(llm, tools)
        result = await agent.execute("Find a restaurant in KLCC, then get directions from my location")
    """
    
    def __init__(self, llm, mcp_manager=None):
        self.llm = llm
        self.mcp_manager = mcp_manager
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Builds the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("plan", self._plan_steps)
        workflow.add_node("execute_step", self._execute_step)
        workflow.add_node("summarize", self._summarize_results)
        
        # Add edges
        workflow.set_entry_point("plan")
        workflow.add_edge("plan", "execute_step")
        workflow.add_conditional_edges(
            "execute_step",
            self._should_continue,
            {
                "continue": "execute_step",
                "done": "summarize"
            }
        )
        workflow.add_edge("summarize", END)
        
        return workflow.compile()
    
    async def _plan_steps(self, state: AgentState) -> AgentState:
        """Plans the steps needed to complete the task."""
        user_message = state["messages"][-1].content
        
        planning_prompt = f"""Break down this request into sequential steps:
"{user_message}"

Return a numbered list of steps. Each step should be actionable.
Example:
1. Search for restaurants in KLCC
2. Filter by rating > 4.0
3. Get directions to the top result

Steps:"""
        
        response = await self.llm.ainvoke(planning_prompt)
        plan_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse steps (simple line-based parsing)
        steps = [line.strip() for line in plan_text.split("\n") if line.strip() and line.strip()[0].isdigit()]
        
        return {
            **state,
            "total_steps": len(steps),
            "current_step": 0,
            "steps_completed": [],
            "messages": state["messages"] + [AIMessage(content=f"Plan:\n{plan_text}")]
        }
    
    async def _execute_step(self, state: AgentState) -> AgentState:
        """Executes the current step."""
        current = state["current_step"]
        
        # Get the step description from the plan
        plan_message = state["messages"][-1].content
        steps = [line.strip() for line in plan_message.split("\n") if line.strip() and line.strip()[0].isdigit()]
        
        if current >= len(steps):
            return state
            
        step_description = steps[current]
        
        # Execute the step using tools
        execution_prompt = f"""Execute this step: {step_description}
        
Use the available tools to complete this task. Be concise."""
        
        # For now, use LLM directly (in production, would route to MCP tools)
        response = await self.llm.ainvoke(execution_prompt)
        result = response.content if hasattr(response, 'content') else str(response)
        
        completed = state["steps_completed"] + [{
            "step": current + 1,
            "description": step_description,
            "result": result
        }]
        
        return {
            **state,
            "current_step": current + 1,
            "steps_completed": completed,
            "messages": state["messages"] + [AIMessage(content=f"Step {current + 1}: {result}")]
        }
    
    def _should_continue(self, state: AgentState) -> str:
        """Determines if we should continue to the next step or finish."""
        if state["current_step"] >= state["total_steps"]:
            return "done"
        return "continue"
    
    async def _summarize_results(self, state: AgentState) -> AgentState:
        """Summarizes all completed steps into a final result."""
        steps_text = "\n".join([
            f"Step {s['step']}: {s['result']}" 
            for s in state["steps_completed"]
        ])
        
        summary_prompt = f"""Summarize the results of these completed steps into a helpful response:

{steps_text}

Provide a natural, conversational summary:"""
        
        response = await self.llm.ainvoke(summary_prompt)
        summary = response.content if hasattr(response, 'content') else str(response)
        
        return {
            **state,
            "final_result": summary,
            "messages": state["messages"] + [AIMessage(content=summary)]
        }
    
    async def execute(self, task: str) -> dict:
        """
        Executes a multi-step task.
        
        Args:
            task: Natural language description of the task
            
        Returns:
            dict with steps_completed and final_result
        """
        initial_state: AgentState = {
            "messages": [HumanMessage(content=task)],
            "current_step": 0,
            "total_steps": 0,
            "steps_completed": [],
            "final_result": None
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "steps": final_state["steps_completed"],
            "result": final_state["final_result"]
        }
