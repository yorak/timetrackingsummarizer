from math import floor
from datetime import datetime, timedelta
from collections import defaultdict
import re


# TODO: modify to use categories for the year, month, day
date_re = re.compile(
    r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Mo|Tu|We|Th|Fr|Sa|Su) +([0-3]?[0-9])\.([01]?[0-9])\.([1|2]?[0-9]?[0-9][0-9])"
)
line_re = re.compile(
    r"(?P<from_hour>[0-9]{1,2})[:\.](?P<from_min>[0-9]{2})"+ # e.g., 9:30
    r"\s*-\s*"+ # from - to (the line)
    r"(?P<to_hour>[0-9]{1,2})[:\.](?P<to_min>[0-9]{2})"+ # e.g., 12.03
    r"(,)?\s+(?P<description>[^\(]+\.?\s*)" # Rest of the line
    #r"\((?P<caterogry>[0-9].[0-9] *[\\\/]? *)*\)"
    #r"\((?P<caterogry>[0-9].[0-9] *[\\\/]? *)*\)"
    #"\((?P<caterogry>.*\.? *)*\)"
)
tag_re = re.compile( r"(\@\w+)" ) # for finding "All @Tags and @Others"
and_tag_re = re.compile( r"and (\@\w+)" ) # matches "and @Tag"

def get_tags(line, tag_translator=lambda tag:tag):
    return [tag_translator(tag) for tag in tag_re.findall(line)]

def is_timelog_line(line):
    """Helper to determine if the line contains timelog data."""
    return True if line_re.match(line) else False

def get_categories_from(line):
    start_cats = line.rfind("(")
    end_cats = line.rfind(")")
    cats = []
    if (start_cats!=-1 and end_cats!=-1):
        cats = [c.strip() 
            for c in re.split(r'/|\+| |, ', line[start_cats+1:end_cats])
            if tag_re.match(c.strip())]
    return cats

def flatten(t):
    return [item for sublist in t for item in sublist]

def parse_and_summarize(lines, only_cat=None, duration_scaler=1.0,
                        also_tags=False,
                        all_tags_replacement=[],
                        tag_translator=lambda tag:tag,
                        do_print=True, min2str=lambda min:int(min)):
    """ Process the lines to timetracking records.

    The parsing is governed by the regular expressions above:
     * `date_re` specifies the format of the dates (identified as date line).
     * `line_re` specifies the format of a timetracking record line.
     * `tag_re` and `and_tag_re` are used to identify additional tags.

    Parameters
    ----------
    lines : `list`
       A sequence (`list`, for example) of lines for the timetracking data.
    only_cat : `str`
       Only durations for this category tag are calculated.
    duration_scaler : `float`
       All times are scaled using this multiplier before printing and storing.
    also_tags : `bool`
       Produce a more detailed data also containing by-tag summaries.
    all_tags_replacement : `list`
       Can be used to alias 'ALL' category to serveral. 
    tag_translator : `callable`
       Can be used to alias tags to another (maybe even serveral).
    do_print : `bool`
       Output summaries to stdout.
    
    Returns
    -------

    """
    daily_minutes, daily_cat_minutes, daily_notes = 0, 0, ""
    prev_date, prev_time_to = "", datetime.fromtimestamp(0)
    dummydt = datetime.now() # Not used, but need to be given to datetime

    total_per_cat = {}
    
    for line in lines:
        try:
            do = date_re.match(line.replace("*",""))
            if do:
                #print("match do", line)
                if daily_minutes>0 and do_print:
                    if only_cat:
                        print(prev_date, min2str(daily_cat_minutes),
                              ":", daily_notes.replace("@", ""), "\n")
                    else:
                        print(prev_date, min2str(daily_minutes))

                daily_minutes, daily_cat_minutes, daily_notes = 0, 0, ""
                prev_date, prev_time_to = line, datetime.fromtimestamp(0)
                continue

            mo = line_re.match(line)
            if mo:
                from_dt = datetime(year=dummydt.year, month=dummydt.month, day=dummydt.day,
                                hour=int(mo.group('from_hour')),
                                minute=int(mo.group('from_min')))
                to_dt   = datetime(year=dummydt.year, month=dummydt.month, day=dummydt.day,
                                hour=int(mo.group('to_hour')),
                                minute=int(mo.group('to_min')))

                if from_dt<prev_time_to and do_print:
                    print("WARNING: Time overlap on", prev_date, "line:", line)     
                prev_time_to = to_dt

                task_duration:timedelta = to_dt-from_dt
                td_min = (task_duration.total_seconds())/60.0*duration_scaler
                daily_minutes += td_min

                cats = get_categories_from(line)
                if '@ALL' in cats and all_tags_replacement:
                    cats+=all_tags_replacement
                    cats.remove('@ALL')
                #print(cats, all_tags_replacement)
                
                if not cats and do_print:
                    print("Warning, no categories on", prev_date, "line:", line)
                
                tags = []
                if also_tags:
                    tags = [tag_translator(tag)
                            for tag in tag_re.findall(line)
                            if tag not in cats]
                    and_tags = [tag_translator(tag)
                                for tag in and_tag_re.findall(line)
                                if tag not in cats]

                    specifier_tags = []
                    activity_tags = []
                    if tags:
                        activity_tags = [tags[0]] + and_tags
                        specifier_tags = [tag for tag in tags[1:]
                                              if tag not in and_tags]
                        # Naively leave out prulars
                        #activity_tags = [t if t[-1]!='s' else t[:-1] for t in activity_tags]
                        #specifier_tags = [t if t[-1]!='s' else t[:-1] for t in specifier_tags]

                for cat in cats:
                    if only_cat and only_cat!=cat:
                        continue # skip all but the tag
                    if not cat in total_per_cat:
                        total_per_cat[cat] = 0 if not also_tags else [0, {}]
                    daily_notes += line[:line.rfind("(")-1].strip("0123456789:.-\t ")+"; "

                    if also_tags and tags:
                        total_per_cat[cat][0]+=td_min/len(cats) 
                        for activity_tag in activity_tags:
                            if not activity_tag in total_per_cat[cat][1]:
                                total_per_cat[cat][1][activity_tag] = [0, defaultdict(int)]
                            total_per_cat[cat][1][activity_tag][0]+=td_min/len(cats)/len(activity_tags)*duration_scaler
                            for s_tag in specifier_tags:
                                total_per_cat[cat][1][activity_tag][1][s_tag] += td_min/len(cats)/len(activity_tags)/len(specifier_tags)*duration_scaler
                    else:
                        total_per_cat[cat]+=td_min/len(cats)

                    daily_cat_minutes+=td_min/len(cats)

        except BaseException as e:
            print( "Problem on line with content: ", line)
            raise e
                    
    if daily_minutes>0 and do_print:
        if only_cat:
            print(prev_date, min2str(daily_cat_minutes), ":", daily_notes.replace("@", ""), "\n")
        else:
            print(prev_date, min2str(daily_minutes))

    return total_per_cat
