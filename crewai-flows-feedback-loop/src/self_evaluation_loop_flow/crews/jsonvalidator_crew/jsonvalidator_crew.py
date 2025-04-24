from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Optional
from pydantic import BaseModel

class JSONVerification(BaseModel):
    valid: bool
    accuracy_score: float
    feedback: Optional[str]


@CrewBase
class JsonvalidatorCrew():
	"""JsonvalidatorCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def sop_json_verifier(self) -> Agent:
		return Agent(
			config=self.agents_config['sop_json_verifier'],
			llm="gpt-4o-2024-11-20",
		)

	@task
	def verify_sop_json(self) -> Task:
		return Task(
			config=self.tasks_config['verify_sop_json'],
			output_pydantic=JSONVerification,
		)


	@crew
	def crew(self) -> Crew:
		"""Creates the JsonvalidatorCrew crew"""

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)
