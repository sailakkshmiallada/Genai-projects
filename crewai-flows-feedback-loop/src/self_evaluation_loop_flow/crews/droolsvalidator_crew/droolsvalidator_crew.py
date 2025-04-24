from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from typing import Optional
from pydantic import BaseModel

class DroolsVerification(BaseModel):
    valid: bool
    accuracy_score: float
    feedback: Optional[str]


@CrewBase
class DroolsvalidatorCrew():
	"""DroolsvalidatorCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def drools_verifier_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['drools_verifier_agent'],
			llm="gpt-4o-2024-11-20",
		)

	@task
	def validate_drools_sop(self) -> Task:
		return Task(
			config=self.tasks_config['validate_drools_sop'],
			output_pydantic=DroolsVerification,
		)


	@crew
	def crew(self) -> Crew:
		"""Creates the DroolsvalidatorCrew crew"""


		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
