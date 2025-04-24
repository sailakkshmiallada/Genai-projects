from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from pydantic import BaseModel, Field


class DroolsSOPModel(BaseModel):
    drools_sop: str = Field(..., description="The complete Drools code containing all rules.")

@CrewBase
class DroolscrafterCrew():
	"""DroolscrafterCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def json_to_drools_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['json_to_drools_agent'],
			llm="gpt-4o-2024-11-20",
		)
	
	@task
	def convert_json_to_drools(self) -> Task:
		return Task(
			config=self.tasks_config['convert_json_to_drools'],
			output_json=DroolsSOPModel
		)


	@crew
	def crew(self) -> Crew:
		"""Creates the DroolscrafterCrew crew"""

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)
