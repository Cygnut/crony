import sys
import os
from datetime import datetime

from crontab import CronTab
import unittest
from parameterized import parameterized, param

import crony.analyser

# A reminder on the cron format:
#
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday;
# │ │ │ │ │                                   7 is also Sunday on some systems)
# │ │ │ │ │
# │ │ │ │ │
# * * * * * <command to execute>

def to_datetime(s, fmt=None):
    return datetime.strptime(s, fmt if fmt else "%Y-%m-%d %H:%M:%S")

def get_job_occurrences(lines, **kwargs):
    return list(crony.analyser.get_job_occurrences(
        CronTab(tab="\n".join(lines)), 
        **kwargs
        ))

class AnalyserTest(unittest.TestCase):
    @parameterized.expand([
        param("every minute",               "* * * * *",   31),      # 00, 01, ... , 30
        param("on the hour",                "0 * * * *",   1),
        param("on begin boundary",          "0 0 * * *",   1),
        param("before begin boundary",      "59 23 * * *", 0),
        param("on end boundary",            "30 0 * * *",  1),        
        param("after end boundary",         "31 0 * * *",  0),
        param("really out of schedule",     "59 11 1 1 0", 0),
        param("disabled, every minute",     "#* * * * *",  0, expected_job_count=0),
        param("disabled, every minute, but including disabled",  
                                            "#* * * * *",  31, expected_job_count=1, include_disabled=True)
    ])
    def test_single_line(self, 
        _, 
        schedule, 
        expected_occurrence_count, 
        begin="2020-01-01 00:00:00",
        end="2020-01-01 00:30:00",
        include_disabled=False,
        expected_job_count=1,
        ):
        expected_command = "it"
        jobs = get_job_occurrences([ 
                f"{schedule} {expected_command}",
            ],
            begin=to_datetime(begin),
            end=to_datetime(end),
            include_disabled=include_disabled
        )

        self.assertEqual(expected_job_count, len(jobs))
        
        if expected_job_count:
            job = jobs[0]
            self.assertEqual(expected_command, job.command)
            self.assertEqual(expected_occurrence_count, len(job.occurrences))

    def test_multi_line(self):
        begin = to_datetime('2020-01-01 00:00:00')
        end = to_datetime('2020-01-01 00:30:00')

        jobs = get_job_occurrences([
                '* * * * * enabled # enabled comment',
                '#* * * * * disabled # disabled comment',
                'invalid_line'
            ],
            begin=begin,
            end=end,
            include_disabled=False      # Gets more coverage
        )

        self.assertEqual(1, len(jobs))
        job = jobs[0]
        self.assertEqual('enabled', job.command)
        self.assertEqual('* * * * * enabled # enabled comment', job.line)
        self.assertEqual(31, len(job.occurrences))

        cur = begin
        expected = []
        while cur <= end:
            expected.append(cur)
            cur += datetime.timedelta(minutes=1)

        # Badly named, this asserts on list length and per-item equality without looking at the order
        self.assertCountEqual(expected, job.occurrences)

    def test_invalid_crontab_handling(self):
        # TODO: Handle this - "59 11 0 0 0" which is an invalid cron line - we should probably update the code to emit this better
        pass