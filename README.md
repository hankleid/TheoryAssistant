Quick installation.

1. Clone this repository.
2. Edit `.claude/skills/problem-background/SKILL.md` with details of the problem you want the agent to help you solve. Include a clear problem statement and definition of success. The agent will always do a literature search on its own, but you may also include here specific knowledge you would like the agent to make use of. You may also wish to specify the level of rigor or process(es) you would like the agent to consider. The level of specificity of this document is up to the human scientist. Less information will result in a more exploratory agent, while more information is useful for a guided analysis.
3. OPTIONAL: under `tools/` add your own Python tools you'd like the agent to use. You may leave it empty if you want the agent to make its own tools. If you have data files, it is helpful to include a tool which opens the files and extracts the data.
4. Start running the agent in `claude_run.py`. Uncomment the line with the step you wish to run.

The steps in `run_claude.py` include the following:
1. **Create Plan**. The agent reads `.claude/skills/problem-background/SKILL.md`, conducts a thorough literature search, then arrives at a research plan. If you don't like the research plan the agent generates at this step, I recommend editing `.claude/skills/problem-background/SKILL.md` to refine the information/goals of the analysis then re-run this step. If there are some inaccuracies or mistakes in the plan, you may consider running the next step before restarting.
2. **Revise Plan**. The agent double checks all technical details of the plan and reviews the citations. It also takes another look at `.claude/skills/problem-background/SKILL.md` to make sure the plan achieves the goal in mind.
3. **Generate Tools**. The agent generates Python tools for achieving all steps of the plan.
4. **Generate Execution Checkpoints**. The agent creates a `.json` file outlining the sequential steps of the research plan. This breaks the research plan into specific phases which are easier for us humans to track while the agent is executing. 
6. **Execute Phase**. The agent assesses the current progress and executes the next phase as outlined by the checkpoints `.json`. You should see the agent's work and results appear under `analysis/phase_[N]/` where `N` is the step number. Once the phase concludes the program stops. You need to run this step once per phase. Check the outputs of each phase if you are interested in how the agentic analysis is going. To assess the agent's fully autonomous capabilities, do not edit any of the agent's work. However for maximizing the likelihood of scientific discovery I think it's fair to make any edits you see fit. If you do so, please record your changes in detail.

For all of these steps, all the agent's actions are recorded in `log.txt`. We use this to analyze the agent for research purposes. By default the log is appended to, not rewritten, so you may want to manually remove/delete the log if you want to start a new run.
The prompts for each step can be found under `prompts/`. Please do not edit these; they constitute the agentic framework itself and changing these will make it hard to compare agent outputs for different problems. `.claude/skills/problem-background/SKILL.md` and `tools/` are where you should be making most of your edits.

Please reach out with comments/questions!
