from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from self_evaluation_loop_flow.tools.CharacterCounterTool import CharacterCounterTool
# If you want to run a snippet of code before or after the crew starts, 
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class ShakespeareCrew():
	"""ShakespeareCrew crew"""

	agents_config = 'config/agents.yaml'
	tasks_config = 'config/tasks.yaml'

	@agent
	def shakespearean_bard(self) -> Agent:
		"""Creates the ShakespeareCrew agent"""
		return Agent(
			config=self.agents_config["shakespearean_bard"],
			tools=[CharacterCounterTool()]
		)
	
	@task
	def write_X_post(self) -> Task:
		"""Creates the ShakespeareCrew task"""
		return Task(
			config=self.tasks_config['write_X_post']
		
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the ShakespeareCrew crew"""
		# To learn how to add knowledge sources to your crew, check out the documentation:
		# https://docs.crewai.com/concepts/knowledge#what-is-knowledge

		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			# process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
		)
