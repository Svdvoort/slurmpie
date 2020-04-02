Tutorial
======================

Job submission
----------------

The most basic usage of slurmpie is to submit a single job.
Lets say we have a script ``slurm_script.sh`` that we want to submit.
Using ``slurmpie`` this is as simple as:

>>> from slurmpie import slurmpie
>>> job = slurmpie.Job("slurm_script.sh")
>>> job.submit()

Job submission with arguments
--------------------------------------

Often one want to set certain parameters for the job such as the partition,
requested memory and wall time.
These parameters can be set at the creation of the job, or set as attributes
after the creation.

For example:

>>> from slurmpie import slurmpie
>>> job = slurmpie.Job("slurm_script.sh", name="my_slurm_job")
>>> job.memory_size = "15GB"
>>> job.partition = "gpu"
>>> job.submit()

This will submit a job with the job name ``my_slurm_job`` and with 15GB of memory requested on the `gpu` partition.
For a full overview of the slurm parameters that can be set, see :py:meth:`slurmpie.slurmpie.Job.__init__`

Job pipeline
----------------------------

Sometimes multiple job depend on each other and one cannot start without the other being finished.
For this, you can use a pipeline.

The simplest pipeline would be:

>>> from slurmpie import slurmpie
>>> job = slurmpie.Job("slurm_script.sh")
>>> followup_job = slurmpie.Job("slurm_followup_script.sh")
>>> pipeline = slurmpie.Pipeline()
>>> pipeline.add(job)
>>> pipeline.add(followup_job)
>>> pipeline.submit()

This will submit ``slurm_script.sh`` and ``slurm_followup_script.sh``, but ``slurm_followup_script.sh``
will only start running once ``slurm_script.sh`` is finished.

Parsing arguments
*************************

To avoid having to repeat the same parameters to each individual job, they can be parsed to the pipeline directly.
For example, instead of:

>>> from slurmpie import slurmpie
>>> job = slurmpie.Job("slurm_script.sh", partition="gpu")
>>> followup_job = slurmpie.Job("slurm_followup_script.sh", partition="gpu")
>>> pipeline = slurmpie.Pipeline()
>>> pipeline.add(job)
>>> pipeline.add(followup_job)
>>> pipeline.submit()

you can do this:

>>> from slurmpie import slurmpie
>>> job = slurmpie.Job("slurm_script.sh")
>>> followup_job = slurmpie.Job("slurm_followup_script.sh")
>>> pipeline = slurmpie.Pipeline(partition="gpu")
>>> pipeline.add(job)
>>> pipeline.add(followup_job)
>>> pipeline.submit()

and all the jobs inthis pipeline wil be submitted to the `gpu` partition.
Attributes that have been set for the job already will not be overwitten.
For example:

>>> from slurmpie import slurmpie
>>> job_1 = slurmpie.Job("slurm_script_1.sh")
>>> job_2 = slurmpie.Job("slurm_script_2.sh", partition="gpu")
>>> job_3 = slurmpie.Job("slurm_script_3.sh")
>>> pipeline = slurmpie.Pipeline(partition="cpu")
>>> pipeline.add(job_1)
>>> pipeline.add(job_2)
>>> pipeline.add(job_3)
>>> pipeline.submit()

will submit ``slurm_script_1.sh`` and ``slurm_script_3.sh`` to the `cpu` partition,
but ``slurm_script_2.sh`` wil be submitted to the gpu partition, as has been specified for the job.

Complex pipelines
*************************

By default the jobs in the pipeline will run in the same order as they have been added to the pipeline.
So in the example above first job_1 will run, once that is finished job_2 will run and once that is finished job_3.
It does not matter whether any of the jobs failed.

To allow for more complex behaviour one can specify the parent job and the dependency type of each job.

For example, lets start with a simple pipeline:

>>> from slurmpie import slurmpie
>>> job_1 = slurmpie.Job("slurm_script_1.sh")
>>> job_2 = slurmpie.Job("slurm_script_2.sh")
>>> pipeline.add(job_1)
>>> pipeline.add(job_2)

If we would submit this pipeline, it will run ``job_2`` as soon as ``job_1`` is finished.
Now, we add a job that will only run if job_1 runs successfully:

>>> job_3 = slurmy.Job("slurm_script_3.sh")
>>> pipeline.add({"afterok": [job_3]}, parent_job=job_1)

If we would submit this pipeline, ``job_3`` will only run if ``job_1`` executed successfully.

Now, we add another job that we want to start at the same time as ``job_1``

>>> job_4 = slurmpie.Job("slurm_script_4.sh")
>>> pipeline.add_start_job(job_4)

If we would the submit the pipeline as it currently is ``job_1`` and ```job_4`` would start immediatly.
Once ``job_1`` finished, ``job_2`` will start running.
If ``job_1`` has finished successfully ``job_3`` will run as well.

Now, lets add a final bit of complexity, if ``job_4`` finishes successfully we want
two other jobs to start.
If it fails we have one other job that we want to start.

First lets create the jobs:

>>> job_5 = slurmpie.Job("slurm_script_5.sh")
>>> job_6 = slurmpie.Job("slurm_script_6.sh")
>>> job_7 = slurmpie.Job("slurm_script_7.sh")

Now we add them to the pipeline:

>>> pipeline.add({"afterok": [job_5, job_6], "afternotok": [job_7]}, parent_job=job_4)

and finally we want the pipeline to start:

>>> pipeline.submit()

``job_5`` and ``job_6`` will now start if ``job_4`` finished successfully.
Otherwise, ``job_7`` will start.

For the full functionality, please see :py:class:`slurmpie.slurmpie.Pipeline`.
For the different dependency types please check out the SLURM documentation: https://slurm.schedmd.com/sbatch.html

