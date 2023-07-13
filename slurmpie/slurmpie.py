import itertools
import math
import numbers
import os
import re
import subprocess
from typing import Dict, Tuple, Union, List


class Job:
    _newid = itertools.count()

    def __init__(
        self,
        script: str,
        script_is_file: bool = True,
        array: Union[str, list] = [],
        cpus_per_task: int = -1,
        error_file: str = "",
        gpus: dict = {},
        gres: dict = {},
        logfile_directory: str = "",
        mail_address: str = "",
        mail_type: str = "",
        memory_size: Union[str, int] = "",
        name: str = "",
        nodes: int = -1,
        nodelist: str = [],
        output_file: str = "",
        partition: str = "",
        tasks: int = -1,
        time: str = "",
        workdir: str = "",
    ):
        """
        A SLURM job which is submitted using sbatch

        Args:
            script (str): The script file or command which the job should execute.
            script_is_file (bool): If the script string is a command to execute directly instead
             of a bash script, set this to False. Defaults to True.
            array (list or str, optional): Optional array parameters to launch multiple jobs.
             When a list is provided a job will be executed with each parameters in the list.
             A string can be provided to allow array construction in the SLURM format.
            cpus_per_task (int, optional): Number of cpus for each task.
            error_file (str, optional): File path for the slurm error file.
            gpus (dict, optional): Specify the gpu requirements for the job. See also gres.
            gres (dict, optional): Specify the gres requirements for the jobs.
             See :func:`slurmpie.slurmpie.Job.gres` for the full specification.
            logfile_directory (str, optional): Set a base directory for the output and error files.
             If this is set, the full paths don't have to be specified for error_file and output_file
            mail_address (str, optional): Mail address to send notifications to.
            mail_type (str, optional): Specify for which events a notification should be send.
             One of: NONE, BEGIN, END, FAIL, REQUEUE, ALL
            memory_size (str or int): Specify memory requirement for job.
             See :func:`slurmpie.slurmpie.Job.memory_size` for the specification.
            name (str, optional): The name of the job.
            nodes (int, optional): Number of nodes to use for the job.
            nodelist (str, optional): Request specific host nodes for job.
            output_file (str, optional): File path for the slurm output file.
            partition (str, optional): Name of the partition to which to submit the job.
            tasks (int, optional): Number of tasks.
            time (str, optional): The expected/maximum wall time for the job.
             Needs to be specified in the SLURM format, one of:
             "minutes", "minutes:seconds", "hours:minutes:seconds",
             "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds"
            workdir (str, optional): The directory to change to at the start of job execution.

        Raises:
            RuntimeError: If the job could not be successfully executed
        """

        self._array = ""
        self._dependencies = ""
        self._gpus = ""
        self._gres = ""
        self._memory_size = ""
        self._memory_units = None
        self._id = next(Job._newid)
        self._nodelist = ""

        self.script = script
        self.script_is_file = script_is_file

        self.array = array
        self.cpus_per_task = cpus_per_task
        self.dependencies = ""
        if logfile_directory == "":
            self.error_file = error_file
        else:
            self.error_file = os.path.join(logfile_directory, error_file)
        self.gpus = gpus
        self.gres = gres
        self.mail_address = mail_address
        self.name = name
        self.nodes = nodes
        if logfile_directory == "":
            self.output_file = output_file
        else:
            self.output_file = os.path.join(logfile_directory, output_file)
        self.partition = partition
        self.tasks = tasks
        self.time = time
        self.workdir = workdir

        if self.mail_address != "" and mail_type == "":
            self.mail_type = "ALL"
        else:
            self.mail_type = mail_type

        if memory_size != "":
            self.memory_size = memory_size

    @staticmethod
    def _format_argument_list(argument_value: str, to_add_argument_values: str) -> str:
        """
        Formats a multi-argument list for SLURM.

        Args:
            argument_value (str): The current value of the argument
            to_add_argument_values (str): The values to add

        Returns:
            str: Concatenated arguments
        """

        if argument_value == "":
            argument_value = to_add_argument_values
        elif to_add_argument_values == "":
            # Dont need to do anything
            pass
        else:
            argument_value += ","
            argument_value += to_add_argument_values
        return argument_value

    @property
    def memory_size(self) -> str:
        """
        The memory size to request for the job.

        Memory size can be set either as a float, then the default memory units
        for the SLURM configuration is used.
        Otherwise, the memory size can specified as a string, including the units.
        For example `"15GB"` will set the request memory to 15 GB.
        Supported memory units are K/KB for kilobyte, M/MB for megabyte
        G/GB for gigabyte and T/TB for terabyte
        """
        memory_size = self._memory_size
        if self._memory_units is not None:
            memory_size += self._memory_units

        return memory_size

    @property
    def memory_units(self) -> str:
        """
        The current memory units
        """
        return self._memory_units

    @staticmethod
    def _format_memory_size(memory_size: Union[int, str]) -> Tuple[str, str]:
        """Formats the memory size to the correct format.

        Memory size can be either given as a float (without units),
        or a string which includes the units.
        This function then correctly formats the memory size and units

        Args:
            memory_size (int or str): The memory size to format

        Returns:
            Tuple[str, str]: The memory size and memory units
        """
        MEMORY_UNITS_MAP = {
            "K": "K",
            "M": "M",
            "G": "G",
            "T": "T",
            "KB": "K",
            "MB": "M",
            "GB": "G",
            "TB": "T",
        }
        memory_units = None

        if isinstance(memory_size, str):
            # Regex to split the number and the units
            splitted_memory = list(filter(None, re.split(r"(\d*\.?\d*)", memory_size)))

            if len(splitted_memory) > 1:
                memory_units = MEMORY_UNITS_MAP[splitted_memory[1]]

            # Here assume float to properly round later
            memory_size = float(splitted_memory[0])

        # Memory size has to be an int
        # We fix this for the user if they specify a float
        memory_size = str(int(math.ceil(memory_size)))

        return memory_size, memory_units

    @memory_size.setter
    def memory_size(self, memory_size: Union[int, str]):
        memory_size, memory_units = self._format_memory_size(memory_size)
        self._memory_size = memory_size
        self._memory_units = memory_units

    @property
    def gres(self) -> str:
        """The gres resources to request for the job.

        The gres resources should be formatted as a (possibly nested) dict.
        For example: `job.gres = {"gpu":1}` requests one gpu from gres.
        `jobs.gres = {"gpu": {"k40": 1, "k80": 1}}` requests one k40 gpu
        and one k80 gpu.
        """
        return self._gres

    def _format_gres(self, gres_spec: dict) -> str:
        """
        Formats the gres specifications from a dict to a SLURM string

        Args:
            gres_spec (dict): Request gres resources

        Returns:
            str: SLURM formated gres string
        """
        out_gres = ""
        # make sure its reproducible
        for key, value in sorted(gres_spec.items(), key=lambda x: x[0].lower()):
            this_gres = str(key) + ":"
            if isinstance(value, dict):
                gres_types = self._format_gres(value).split(",")

                this_gres = [this_gres + i_type for i_type in gres_types]
                this_gres = ",".join(this_gres)

            else:
                this_gres += str(value)
            out_gres = self._format_argument_list(out_gres, this_gres)
        return out_gres

    @gres.setter
    def gres(self, gres_spec: dict):
        self._gres = self._format_argument_list(
            self._gres, self._format_gres(gres_spec)
        )

    def depends_on(self, job_id: Union[list, str], dependency_type="afterany"):
        """
        Sets the dependencies of this job based on the SLURM job number.

        When submitting a job that depends on another job this can be set
        using the job id of the job.

        Example:
            >>> from slurmpie import slurmpie
            >>> job = slurmpie.Job("slurm_script.sh")
            >>> dependent_job = slurmpie.Job("slurm_script_2.sh")
            >>> job_id = job.submit()
            >>> dependent_job.depends_on(job_id)
            >>> dependent_job.submit()

            The `dependent_job` will now only start running when `job` has finished.

        Args:
            job_id (list or str): The job id (or multiple ids as a list) on which the job depends.
            dependency_type (str, optional): The dependency type of the job (see
             sbatch documentation). Defaults to "afterany".
        """

        if isinstance(job_id, list):
            job_id = ":".join(job_id)

        dependency = "{}:{}".format(dependency_type, job_id)

        self.dependencies = self._format_argument_list(self.dependencies, dependency)

    @property
    def array(self) -> str:
        """
        The values of the job array.

        SLURM supports submitting the same script with different parameters.
        Set the array either as a list of values or as a string.
        When specified as string it is directly parsed to SLURM, thus the string
        should already be in the SLURM format.
        When a list is specified it will parse all these values to the array
        setting.
        """
        return self._array

    @array.setter
    def array(self, array_spec: Union[list, str]):
        if isinstance(array_spec, list):
            array_spec = [str(i_spec) for i_spec in array_spec]
            array_spec = ",".join(array_spec)

        self._array = self._format_argument_list(self._array, array_spec)

    @property
    def nodelist(self) -> str:
        """
        List of nodes to run the job on.

        When you want to run a job on a specific node (that is not specified by a queue),
        you can use this argument to specify the exact nodes you want to run
        the job on.
        """

        return self._nodelist

    @nodelist.setter
    def nodelist(self, nodelist_spec: str):
        self._nodelist = nodelist_spec


    @property
    def gpus(self) -> str:
        """
        The gpus to request from the SLURM jobs.

        Just like the gres resources, one can request the gpu resources for the job.
        This is configuration dependent, so make sure your cluster supports this.
        The configuration has to be applied in the same way as for gres.

        """
        return self._gpus

    @gpus.setter
    def gpus(self, gpu_spec: dict):
        self._gpus = self._format_argument_list(self._gpus, self._format_gres(gpu_spec))

    @staticmethod
    def attribute_is_empty(attribute_value: Union[str, numbers.Number, dict, list]) -> bool:
        """
        Checks whether an attribute is empty

        Args:
            attribute_value (str, numbers.Number, dict, or list]): The value to check

        Returns:
            bool: True if attribute is empty,false otherwise.
        """
        if isinstance(attribute_value, str) and attribute_value == "":
            return True
        elif isinstance(attribute_value, numbers.Number) and attribute_value == -1:
            return True
        elif isinstance(attribute_value, dict) and attribute_value == {}:
            return True
        elif isinstance(attribute_value, list) and attribute_value == []:
            return True
        else:
            return False

    def _format_sbatch_command(self) -> list:
        """
        Formats the command for sbatch from the job settings.

        Returns:
            list: Formatted command with one argument per item.
        """

        command_mapping = {
            "array": "array",
            "cpus_per_task": "cpus-per-task",
            "dependencies": "dependency",
            "error_file": "error",
            "gpus": "gpus",
            "gres": "gres",
            "mail_address": "mail-user",
            "mail_type": "mail-type",
            "memory_size": "mem",
            "name": "job-name",
            "nodes": "nodes",
            "output_file": "output",
            "partition": "partition",
            "tasks": "ntasks",
            "time": "time",
            "workdir": "chdir",
            "nodelist": "nodelist"
        }

        # We set parsable to easily get job id
        command = ["sbatch", "--parsable"]

        for attribute_name, bash_argument in sorted(
            command_mapping.items(), key=lambda x: x[0].lower()
        ):
            attribute_value = getattr(self, attribute_name)
            if not self.attribute_is_empty(attribute_value):
                command.append("--{}={}".format(bash_argument, attribute_value))

        if self.script_is_file:
            command.append(self.script)
        else:
            command.append("--wrap={}".format(self.script))

        return command

    def submit(self) -> str:
        """
        Submit the job using `sbatch`

        Raises:
            RuntimeError: If `sbatch` returns an error

        Returns:
            str: The job number of the submitted job if successful
        """

        # The submission is not currently tested, since it requires a slurm install
        # Perhaps a docker with slurm pre-installed is a good idea in this case
        sbatch_command = self._format_sbatch_command()
        sbatch_process = subprocess.Popen(
            sbatch_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        stdout, stderr = sbatch_process.communicate()

        if sbatch_process.returncode != 0:
            err_msg = "Sbatch job submission failed with follow error:\n{}"
            raise RuntimeError(err_msg.format(stderr))
            job_number = None
        else:
            job_number = stdout.decode("utf-8").strip().split(":")[0]
        return job_number


class Pipeline:
    """
    Examples:
        Simple pipeline in which jobs are added consecutively.

            .. literalinclude:: /examples/example_simple_pipeline.py

    """

    def __init__(self, common_job_header=None, **kwargs):
        """
        Pipeline to be constructed with multiple jobs depending on each other.

        This pipeline makes it easier to create multiple job that depend on each
        other and submit them all at ones. Jobs can be added to the pipeline
        with different dependencies and the pipeline can then be submitted
        as a whole, which will take care off the dependencies between the
        different jobs.

        Args:
            common_job_header (str): In case the command to execute is
             direct command (not a file), this will be prepended to every job.
            kwargs: Arguments that will be specified for each job,
             if that argument has not been set for the job already.
        """
        # kwargs will be forwared to individual jobs
        self.job_args = kwargs
        self.pipeline_jobs = list()
        self._job_graph = {-1: []}
        self.common_job_header = common_job_header

    def _update_job_graph(self, parent_id: Union[str, list], jobs: dict):
        """
        Add new jobs to the graph to execute.

        Args:
            parent_id (str): The ID of the parent job (not submission ID!).
            jobs (dict): Jobs that depend on the parent job, with specified dependency type.
        """

        if parent_id == -1:
            self._job_graph[parent_id].extend(list(itertools.chain(*jobs.values())))
        else:
            if isinstance(parent_id, str) or isinstance(parent_id, int):
                parent_id = [parent_id]
            for i_key, i_value in jobs.items():
                for i_job in i_value:
                    if i_job not in self._job_graph:
                        self._job_graph[i_job] = {i_key: parent_id}
                    elif i_key not in self._job_graph[i_job]:
                        self._job_graph[i_job][i_key] = parent_id
                    else:
                        self._job_graph[i_job][i_key].extend(parent_id)

    def add(self, jobs: Union[Job, Dict[str, list]], parent_job: Union[Job, list] = None):
        """
        Add dependency jobs to the pipeline.

        Jobs can keep being added, in which case they are execute consecutively.
        Otherwise, a dict can be specified with the job dependency type and list
        of the jobs with that dependency type.
        A parent job can be set if the jobs depend on a certain parent job.
        Otherwise the jobs will just be added to the end of the list and are
        executed consecutively.

        Args:
            jobs (Job or dict): The jobs to add to the pipeline. Either a single job
             which will be added to the end of the pipeline, or a dict specifying the
             dependency type and a list with the dependent jobs
            parent_job (Job or list, optional): If not None, will use this as the job on which the
             `jobs` are dependent, a list in case of multiple parent jobs. Defaults to None.
        """

        # We accept a single job as ease-of-use for the user
        # Convert it here to make the operation consistent
        if isinstance(jobs, Job):
            jobs = {"afterany": [jobs]}

        if parent_job is not None:
            if isinstance(parent_job, Job):
                parent_id = parent_job._id
            elif isinstance(parent_job, list):
                parent_id = [i_parent_job._id for i_parent_job in parent_job]
        elif len(self.pipeline_jobs) > 0:
            parent_id = self.pipeline_jobs[-1]._id
        else:
            parent_id = -1

        for i_job_dependency_type, i_job_list in jobs.items():
            for i_job in i_job_list:
                # Set arguments from the pipeline if the job does not have them
                # If the job does have them, they take precedence over what is defined
                # in the pipeline.
                for attribute_name, attribute_value in self.job_args.items():
                    if i_job.attribute_is_empty(getattr(i_job, attribute_name)):
                        setattr(i_job, attribute_name, attribute_value)
                if self.common_job_header is not None and not i_job.script_is_file:
                    i_job.script = self.common_job_header + " " + i_job.script

                self.pipeline_jobs.append(i_job)

        self._update_job_graph(parent_id, jobs)

    def add_start_job(self, jobs: Union[Job, list]):
        """
        Add a job to the start of the pipeline

        Args:
            jobs (Job or list): A single job or list of jobs that should be
             executed at the start of the pipeline.
        """
        if isinstance(jobs, Job):
            jobs = [jobs]
        self._update_job_graph(-1, {"begin": jobs})

    def submit(self):
        """
        Submit all the jobs in the pipeline.

        Raises:
            RecursionError: If the pipeline cannot be properly executed because of
             misformatted dependencies.
        """
        # First submit all the start jobs
        submission_info = dict()
        prev_job_graph_len = len(self._job_graph)
        start_jobs = self._job_graph.pop(-1)
        for i_start_job in start_jobs:
            i_submitted_id = i_start_job.submit()
            submission_info[i_start_job._id] = i_submitted_id

        cur_job_graph_len = len(self._job_graph)
        while cur_job_graph_len > 0 and cur_job_graph_len < prev_job_graph_len:
            submitted_jobs = list()
            for job, job_dependencies in self._job_graph.items():
                flat_dependencies = set(itertools.chain(*job_dependencies.values()))
                if flat_dependencies.issubset(set(submission_info.keys())):
                    for dependency_type, parent_id in job_dependencies.items():
                        parent_submitted_job_ids = [
                            submission_info[i_id] for i_id in parent_id
                        ]
                        job.depends_on(parent_submitted_job_ids, dependency_type)
                    job_submission_id = job.submit()
                    submission_info[job._id] = job_submission_id
                    submitted_jobs.append(job)

            for i_submitted_job in submitted_jobs:
                self._job_graph.pop(i_submitted_job)

            prev_job_graph_len = cur_job_graph_len
            cur_job_graph_len = len(self._job_graph)

        if cur_job_graph_len > 0:
            raise RecursionError(
                "You have set impossible to execute job dependencies!\nPlease check your pipeline."
            )

class System:
    def __init__(self):
        """
        Get system information of the SLURM cluster
        """

    def get_job_memory(self) -> Union[int, None]:
        """
        Get the memory available to the job

        Returns:
            int or None: The memory size in kilobytes, None if the SLURM
             memory amount cannot be determined
        """
        if "SLURM_MEM_PER_NODE" in os.environ:
            memory_size = int(os.environ["SLURM_MEM_PER_NODE"])
        else:
            memory_size = None

        return memory_size

