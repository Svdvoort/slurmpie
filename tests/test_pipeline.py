from slurmpy import slurmpy
import pytest


def test_init():
    slurmpy.Pipeline()

    pipeline = slurmpy.Pipeline(name="test_pipeline")
    assert pipeline.job_args == {"name": "test_pipeline"}


def test_job_adding():
    pipeline = slurmpy.Pipeline()

    job = slurmpy.Job("none")
    pipeline.add(job)
    second_job = slurmpy.Job("none")
    pipeline.add(second_job)

    assert isinstance(pipeline.pipeline_jobs, list)
    assert len(pipeline.pipeline_jobs) == 2
    assert pipeline._job_graph == {-1: [job], second_job: {"after": [job._id]}}


def test_job_adding_with_job_arguments():
    job = slurmpy.Job("none")
    pipeline = slurmpy.Pipeline(name="test_pipeline", memory_size="10GB")

    pipeline.add(job)
    pipeline.add(job)

    for job in pipeline.pipeline_jobs:
        assert job.name == "test_pipeline"
        assert job.memory_size == "10G"

    job_with_args = slurmpy.Job("none", name="final_job", memory_size="15MB")
    pipeline.add(job_with_args)

    for job in pipeline.pipeline_jobs[:-1]:
        assert job.name == "test_pipeline"
        assert job.memory_size == "10G"

    assert pipeline.pipeline_jobs[-1].name == "final_job"
    assert pipeline.pipeline_jobs[-1].memory_size == "15M"


def test_start_job_adding():
    job = slurmpy.Job("none")
    pipeline = slurmpy.Pipeline()

    pipeline.add(job)

    success_job = slurmpy.Job("none")
    pipeline.add(success_job)

    second_start_job = slurmpy.Job("none")
    pipeline.add_start_job(second_start_job)

    assert pipeline._job_graph == {
        -1: [job, second_start_job],
        success_job: {"after": [job._id]},
    }


def test_complex_job_adding():
    job = slurmpy.Job("none")
    pipeline = slurmpy.Pipeline()

    pipeline.add(job)
    assert pipeline._job_graph == {-1: [job]}

    second_job = slurmpy.Job("none")
    pipeline.add({"afterok": [second_job]})

    assert isinstance(pipeline.pipeline_jobs, list)
    assert len(pipeline.pipeline_jobs) == 2

    assert pipeline._job_graph == {-1: [job], second_job: {"afterok": [job._id]}}

    fail_job = slurmpy.Job("none")
    pipeline.add({"afternotok": [fail_job]}, job)

    assert pipeline._job_graph == {
        -1: [job],
        second_job: {"afterok": [job._id]},
        fail_job: {"afternotok": [job._id]}
    }

    second_succes_job = slurmpy.Job("none")
    pipeline.add({"afterok": [second_succes_job]}, job)
    assert pipeline._job_graph == {
        -1: [job],
        second_job: {"afterok": [job._id]},
        fail_job: {"afternotok": [job._id]},
        second_succes_job: {"afterok": [job._id]}
    }

    final_job = slurmpy.Job("none")
    pipeline.add(final_job)

    assert pipeline._job_graph == {
        -1: [job],
        second_job: {"afterok": [job._id]},
        fail_job: {"afternotok": [job._id]},
        second_succes_job: {"afterok": [job._id]},
        final_job: {"after": [second_succes_job._id]}
    }

    pipeline.add(fail_job, second_job)

    assert pipeline._job_graph == {
        -1: [job],
        second_job: {"afterok": [job._id]},
        fail_job: {"afternotok": [job._id], "after": [second_job._id]},
        second_succes_job: {"afterok": [job._id]},
        final_job: {"after": [second_succes_job._id]}
    }

    pipeline.add(fail_job, second_succes_job)
    assert pipeline._job_graph == {
        -1: [job],
        second_job: {"afterok": [job._id]},
        fail_job: {"afternotok": [job._id], "after": [second_job._id, second_succes_job._id]},
        second_succes_job: {"afterok": [job._id]},
        final_job: {"after": [second_succes_job._id]}
    }

# These tests only work when slurm is installed

# def test_submit():
#     pipeline = slurmpy.Pipeline()

#     job = slurmpy.Job("none")
#     pipeline.add(job)
#     second_job = slurmpy.Job("none")
#     pipeline.add(second_job)

#     pipeline.submit()


# def test_submit_error():
#     with pytest.raises(RecursionError):
#         pipeline = slurmpy.Pipeline()

#         job = slurmpy.Job("none")
#         pipeline.add(job)
#         second_job = slurmpy.Job("none")
#         third_job = slurmpy.Job("none")
#         pipeline.add(second_job, third_job)
#         pipeline.add(third_job, second_job)

#         pipeline.submit()
