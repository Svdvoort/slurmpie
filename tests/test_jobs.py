import pytest
from slurmpie import slurmpie
import os

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data",
)


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_init(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)
    job_2 = slurmpie.Job(script_file)
    assert job._id != job_2._id

    job = slurmpie.Job(script_file, mail_address="user@example.com")
    assert job.mail_type == "ALL"

    job = slurmpie.Job(script_file, mail_address="user@example.com", mail_type="FAIL")
    assert job.mail_type == "FAIL"

    job = slurmpie.Job(script_file, memory_size="50GB")
    assert job.memory_size == "50G"


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_argument_list_formatting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    assert job._format_argument_list("", "") == ""
    assert job._format_argument_list("", "new_value") == "new_value"
    assert job._format_argument_list("old_value", "") == "old_value"
    assert job._format_argument_list("old_value", "new_value") == "old_value,new_value"
    assert job._format_argument_list("gpu:1", "cpu:3") == "gpu:1,cpu:3"
    assert job._format_argument_list("gpu:1,cpu:3", "ssd:4") == "gpu:1,cpu:3,ssd:4"


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_gres_formatting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    assert job._format_gres({}) == ""
    assert job._format_gres({"gpu": 1}) == "gpu:1"
    assert job._format_gres({"gpu": 1, "ssd": 3}) == "gpu:1,ssd:3"
    assert job._format_gres({"gpu": {"Titan": 3, "k40": 2}}) == "gpu:k40:2,gpu:Titan:3"
    assert (
        job._format_gres({"gpu": {"Titan": 3, "k40": 2}, "ssd": 3})
        == "gpu:k40:2,gpu:Titan:3,ssd:3"
    )
    assert (
        job._format_gres(
            {"gpu": {"Titan": 3, "k40": 2}, "ssd": {"fast": 2, "slow": 1}, "cpu": 15}
        )
        == "cpu:15,gpu:k40:2,gpu:Titan:3,ssd:fast:2,ssd:slow:1"
    )


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_gres_settting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    job.gres = {}
    assert job.gres == ""

    job = slurmpie.Job(script_file)
    job.gres = {"gpu": 1}
    assert job.gres == "gpu:1"

    job = slurmpie.Job(script_file)
    job.gres = {"gpu": 1, "ssd": 3}
    assert job.gres == "gpu:1,ssd:3"

    job = slurmpie.Job(script_file)
    job.gres = {"gpu": {"Titan": 3, "k40": 2}}
    assert job.gres == "gpu:k40:2,gpu:Titan:3"

    job = slurmpie.Job(script_file)
    job.gres = {"gpu": {"Titan": 3, "k40": 2}, "ssd": 3}
    assert job.gres == "gpu:k40:2,gpu:Titan:3,ssd:3"

    job = slurmpie.Job(script_file)
    job.gres = {"gpu": {"Titan": 3, "k40": 2}, "ssd": {"fast": 2, "slow": 1}, "cpu": 15}
    assert job.gres == "cpu:15,gpu:k40:2,gpu:Titan:3,ssd:fast:2,ssd:slow:1"


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_memory_formatting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    memory_size, memory_units = job._format_memory_size("50M")
    assert memory_size == "50"
    assert memory_units == "M"

    memory_size, memory_units = job._format_memory_size("100.5GB")
    assert memory_size == "101"
    assert memory_units == "G"

    memory_size, memory_units = job._format_memory_size(103)
    assert memory_size == "103"
    assert memory_units is None

    memory_size, memory_units = job._format_memory_size("25000")
    assert memory_size == "25000"
    assert memory_units is None


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_memory_setting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    assert job.memory_size == ""
    assert job.memory_units is None

    job.memory_size = "500MB"

    assert job.memory_size == "500M"
    assert job.memory_units == "M"

    job.memory_size = 213.5

    assert job.memory_size == "214"
    assert job.memory_units is None


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_job_dependencies(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    assert job.dependencies == ""

    job = slurmpie.Job(script_file)
    job.depends_on("40904")
    assert job.dependencies == "afterany:40904"

    job = slurmpie.Job(script_file)
    job.depends_on("9040294", "afterok")
    assert job.dependencies == "afterok:9040294"

    job = slurmpie.Job(script_file)
    job.depends_on(["1001", "9040294"], "afterok")
    assert job.dependencies == "afterok:1001:9040294"

    job = slurmpie.Job(script_file)
    job.depends_on(["1001", "9040294"], "afterok")
    job.depends_on("123", "afternotok")

    assert job.dependencies == "afterok:1001:9040294,afternotok:123"

    job = slurmpie.Job(script_file)
    job.depends_on(["1001", "9040294"], "afterok")
    job.depends_on("123", "afternotok")
    job.depends_on("987", "afterok")

    assert job.dependencies == "afterok:1001:9040294,afternotok:123,afterok:987"


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_array_setting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)
    assert job.array == ""

    job = slurmpie.Job(script_file)
    job.array = [5, 9, 10]
    assert job.array == "5,9,10"

    job = slurmpie.Job(script_file)
    job.array = ["1", "5", "101"]
    assert job.array == "1,5,101"

    job = slurmpie.Job(script_file)
    job.array = "0-15%4"
    assert job.array == "0-15%4"


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_gpu_setting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)
    assert job.gpus == ""

    job = slurmpie.Job(script_file)
    job.gpus = {"Titan": 5}
    assert job.gpus == "Titan:5"

    job = slurmpie.Job(script_file)
    job.gpus = {"Titan": 5, "k40": "3"}
    assert job.gpus == "k40:3,Titan:5"


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_empty_attributes(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    assert job.attribute_is_empty("")
    assert job.attribute_is_empty(-1)
    assert job.attribute_is_empty(-1.0)
    assert job.attribute_is_empty({})
    assert job.attribute_is_empty([])
    assert not job.attribute_is_empty("-1")
    assert not job.attribute_is_empty([""])
    assert not job.attribute_is_empty({"a": "b"})
    assert not job.attribute_is_empty([-1])


@pytest.mark.datafiles(
    os.path.join(FIXTURE_DIR, "slurm_script.sh"),
)
def test_sbatch_formatting(datafiles):
    script_file = str(datafiles)
    job = slurmpie.Job(script_file)

    sbatch_command = job._format_sbatch_command()
    assert sbatch_command == " ".join(["sbatch", "--parsable", script_file])

    job.memory_size = 50

    sbatch_command = job._format_sbatch_command()
    assert sbatch_command == " ".join(["sbatch", "--parsable", "--mem=50", script_file])

    job.gres = {"gpu": {"Titan": 1, "k40": 2}}

    assert job._format_sbatch_command() == " ".join(
        [
            "sbatch",
            "--parsable",
            "--gres=gpu:k40:2,gpu:Titan:1",
            "--mem=50",
            script_file,
        ]
    )

    job = slurmpie.Job(script_file, memory_size="100GB", name="test_job")
    assert job._format_sbatch_command() == " ".join(
        [
            "sbatch",
            "--parsable",
            "--mem=100G",
            "--job-name=test_job",
            script_file,
        ]
    )

    job = slurmpie.Job(
        script_file,
        array=[1, 2, 3],
        cpus_per_task=5,
        error_file="/tmp/error.log",
        gpus={"Titan": 8},
        gres={"cpus": {"haskell": 2, "lake": "3"}},
        mail_address="user@example.com",
        mail_type="FAIL",
        memory_size="10KB",
        name="test_job",
        nodes=4,
        nodelist="cpu001",
        exclude=["gpu001", "mem001"],
        output_file="/tmp/output.log",
        partition="test_partition",
        tasks=7,
        time="01:33",
        workdir="/tmp/workdir",
    )

    assert job._format_sbatch_command() == " ".join(
        [
            "sbatch",
            "--parsable",
            "--array=1,2,3",
            "--cpus-per-task=5",
            "--error=/tmp/error.log",
            "--exclude=gpu001,mem001",
            "--gpus=Titan:8",
            "--gres=cpus:haskell:2,cpus:lake:3",
            "--mail-user=user@example.com",
            "--mail-type=FAIL",
            "--mem=10K",
            "--job-name=test_job",
            "--nodelist=cpu001",
            "--nodes=4",
            "--output=/tmp/output.log",
            "--partition=test_partition",
            "--ntasks=7",
            "--time=01:33",
            "--chdir=/tmp/workdir",
            script_file,
        ]
    )
