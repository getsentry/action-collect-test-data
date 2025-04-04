from __future__ import annotations

import set_job_vars


def test_json_compact():

    assert set_job_vars.json_compact(json_doc="""
                                     [
                                         1,
                                         2
                                         ]""") == "[1,2]"
