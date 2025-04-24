from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel

class JSONContent(BaseModel):
    json_sop: dict


@CrewBase
class JsoncrafterCrew():
	"""JsoncrafterCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def sop_structure_agent(self) -> Agent:
		return Agent(
			config=self.agents_config['sop_structure_agent'],
			llm="gpt-4o-2024-11-20",
		)

	@task
	def convert_sop_to_json(self) -> Task:
		return Task(
			config=self.tasks_config['convert_sop_to_json'],
			output_json=JSONContent,
		)


	@crew
	def crew(self) -> Crew:
		"""Creates the JsoncrafterCrew crew"""

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
		)
