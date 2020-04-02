from slurmpy import slurmpy

pipeline = slurmpy.Pipeline()
start_job = slurmpy.Job("slurm_script.sh")
dependent_job = slurmpy.Job("slurm_script_2.sh")

pipeline.add(start_job)
# This job will wait for start_job to finish
pipeline.add(dependent_job)

pipeline.submit()
