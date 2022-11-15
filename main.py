from glob import glob
from collections import Counter
from math import floor
import argparse

import lineparser

def min2str(total_minutes, in_part_hours=True):
    """Helper to convert minutes to hours (either to "2.50" or "2:30")."""
    if in_part_hours:
        return ("%.2f"%(total_minutes/60.0)).replace(".", ",")
    else:
        total_hours = floor(total_minutes/60)
        remaining_minutes = int(total_minutes-total_hours*60)
        return f"{total_hours}:{remaining_minutes:02d}"

def _filter_lines(all_lines, line_incls, line_excls):
    """Helper to do line filtering using include and exclude lists."""
    filtered_lines = []
    for l in all_lines:
        if not lineparser.is_timelog_line(l):
            filtered_lines.append(l)
        elif line_incls and all( [(lf in l) for lf in line_incls] ):
            if not line_excls or all( [(not lf in l) for lf in line_excls] ):
                filtered_lines.append(l)
        elif line_excls:
            if all( [(not lf in l) for lf in line_excls] ):
                filtered_lines.append(l)
                
    return filtered_lines

if __name__=='__main__':
    argparser = argparse.ArgumentParser(description=
        'Calculates the sum of worked hours on a timesheet from stdin.\n'+
        'Valid lines are of the format "12.03-13:52 @Did a lot ( @CAT )".\n'+
        'Where the "@CAT" is the project / job category and "@Did" is a tag.".\n'+
        'Remember that on Windows Ctrl+Z <ENTER> ends stdin input.' )
    argparser.add_argument("file_name", nargs='+')
    argparser.add_argument("--cat", dest='cat', help="Only show this category/project")
    argparser.add_argument("--lnincl", dest='line_incls', action='append', help="Only consider records with this text")
    argparser.add_argument("--lnexcl", dest='line_excls', action='append', help="Only consider records with this text")
    argparser.add_argument("--show_included", dest='show_included', action='store_true', help="Show included lines")
    argparser.add_argument("--s2m", dest='scale_to_mins', help="Scale minutes so that the total is this")
    argparser.add_argument("--snakey", dest='plot_snakey', action='store_true', help="Produce a snakey plot")
    argparser.add_argument("--no_snakey_specifiers", dest='no_snakey_specifiers', action='store_true', help="Hide specifiers from snakey plot")
    argparser.add_argument("--activity", dest='by_activity', action='store_true', help="Show by activity")
    argparser.add_argument("--count_tags", dest='count_tags', action='store_true', help="Only show tags and their counts")
    argparser.add_argument('--taf', dest='tag_alias_file', type=argparse.FileType('r'), help="A text file with each line containing some @ReadTag=@Alias rule")
    args = argparser.parse_args()
    
    # read all lines from all files to this list
    all_lines = [] 
    for fn in args.file_name:
        # Glob if there is wildcards present
        if '*' in fn or '?' in fn:
            for globbed_fn in glob(fn):
                all_lines+=open(globbed_fn).readlines()
        else:
            all_lines+=open(fn).readlines()
    if args.line_incls or args.line_excls:
        all_lines = _filter_lines(all_lines, args.line_incls, args.line_excls)
        if args.show_included:
            for l in all_lines: print(l)
            

    tag_alias_rules = {}
    if args.tag_alias_file:
        for alias_line in args.tag_alias_file.readlines():
            parts = alias_line.split(", =")
            if len(parts)!=2: continue
            from_tag, to_tag = parts
            tag_alias_rules[from_tag] = to_tag
    def tag_to_tag(tag):
        return tag if tag not in tag_alias_rules else tag_alias_rules[tag]
    
    if args.count_tags:
        tag_counts = Counter()
        for line in all_lines:
            tags = lineparser.get_tags(line, tag_to_tag)
            if tags:
                tag_counts.update(tags)
        for tag, tag_count in tag_counts.most_common():
            print(tag_count, tag)
        exit()

    # Check for special tag
    ALL_tag_cats = []
    all_cats = set()
    for line in all_lines:
        if lineparser.is_timelog_line(line):            
            all_cats = all_cats.union(lineparser.get_categories_from(line))
    if '@ALL' in all_cats:
        all_cats.remove('@ALL')
        ALL_tag_cats = list(all_cats)

    if args.plot_snakey:
        ttpc = lineparser.parse_and_summarize(all_lines, args.cat,
            also_tags=True, tag_translator=tag_to_tag, do_print=False )
        from timetracking_snakey_plotter import plot_timetracking_data
        plot_timetracking_data(ttpc, not args.no_snakey_specifiers)

    if args.by_activity:
        print("BY ACTIVITY:")
        ttpc = lineparser.parse_and_summarize(all_lines, args.cat,
            also_tags=True, tag_translator=tag_to_tag, do_print=False )

        
        for cat, cat_data in sorted(ttpc.items()):
            cat_minutes, activities = cat_data
            print("CAT", cat, min2str(int(cat_minutes)))
            for act, act_data in sorted(activities.items()):
                act_minutes, _ = act_data
                if act_minutes>0:
                    percentage = act_minutes/cat_minutes*100
                    act_hourss = min2str(int(act_minutes))
                    print(f"  {act} {act_hourss} ({percentage:.1f}%)")
            

    else:
        min_scaler = 1.0
        if args.scale_to_mins:
            total_mins = sum( lineparser.parse_and_summarize(all_lines, args.cat, 
                        all_tags_replacement=ALL_tag_cats, do_print=False).values() )
            min_scaler = float(args.scale_to_mins)/total_mins
        
        tpc = lineparser.parse_and_summarize(all_lines, args.cat, 
                duration_scaler=min_scaler,
                all_tags_replacement=ALL_tag_cats,
                min2str=min2str ) 
        print()
        print("TOTAL:")
        tot_tot_mins = 0
        for cat, cat_minutes in sorted(tpc.items()):
            print(cat, min2str(int(cat_minutes)))
            #print(cat, "%.2f"%(cat_minutes/(22*7.5*60)))
            tot_tot_mins+=cat_minutes
        print("TOTALTOTAL:", min2str(int(tot_tot_mins)))
        