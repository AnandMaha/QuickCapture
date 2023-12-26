# Input: Text, Output: Start date, End date, frequency outlined in Text  
import spacy
from datetime import datetime
from datetime import timedelta
from datetime import date
import parsedatetime as pdt 
from word2number import w2n


spacy.require_cpu()
nlp = spacy.load("en_core_web_lg")
ruler = nlp.add_pipe("entity_ruler","ruleActions", config={"overwrite_ents": True})

#s = 'Plan a vacation 26 times every other year on February until feb 2032 for three minutes'
def quickCapture(s):
    fb = {"day":0,"week":0,"month":0,"quarter":0,"year":0} # frequency buckets

    def tr(bucket, amt): # assign freq value to frequency buckets
        fb[bucket] = amt
        
    start_befores = ["from","on",'beginning on', 'commencing', 'starting from', "starting",'inaugurating', 'initiating', 'launching on', 'opening on', 'originating', 'setting out', 'starting off', 'undertaking', 'embarking', 'kickstarting', 'triggering on', \
        'genesis on', 'outset', 'onset', 'introduction', 'premiere','at',"beginning","in"]
    end_befores = ["till","until",'ending on', 'concluding on', 'finishing', 'terminating', 'ceasing on', 'closing', 'culminating', 'finalizing', 'wrapping up', 'halting', 'completing', 'discontinuing on', 'finale on', 'expiring', 'running up to', \
        'ushering out', 'climaxing', 'lasting until', 'terminating','to',"ending","till","end"]
    frequencies = {"daily":lambda:tr("day",1), "weekly":lambda:tr("week",1), "biweekly":lambda:tr("week",2), "monthly":lambda:tr("month",1), "quarterly":lambda:tr("quarter",1),"every day":lambda:tr("day",1),"everyday":lambda:tr("day",1),\
        "every quarter":lambda:tr("quarter",1),"annually":lambda:tr("year",1), "every other day":lambda:tr("day",2), "every 3 days":lambda:tr("day",3), "every 4 days":lambda:tr("day",4), "every 5 days":lambda:tr("day",5),\
        "every 6 days":lambda:tr("day",6), "every 7 days":lambda:tr("day",7),"once every other week":lambda:tr("week",2),"every week":lambda:tr("week",1),"every 2 weeks":lambda:tr("week",2),"every friday":lambda:tr("week",1),\
        "every month":lambda:tr("month",1),"every year":lambda:tr("year",1),"every other year":lambda:tr("year",2)}
    date_words = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday","today", "tomorrow", "this quarter","next quarter","the day after tomorrow", "in 3 days", "in 4 days", "in 5 days", "next week", "in 2 weeks", "in 3 weeks", \
        "next month", "in 2 months", "in 3 months", "in 6 months", "next year", "in 2 years", "in 5 years","end of the year","end of the day","end of the week"]


    # start_before DATE start_before? TIME? -- merged
    patterns = [
        # Date -- Time
        {"label": "DateTime", "pattern": [{"LEMMA": {"IN": date_words}}, {"LEMMA": {"IN": start_befores}, "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}]},
        {"label": "DateTime", "pattern": [{"LEMMA": {"IN": date_words}}, {"LEMMA": {"IN": end_befores}, "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}]},
        {"label": "DateTime", "pattern": [{"ENT_TYPE": "DATE", "OP": "+"}, {"LEMMA": {"IN": start_befores}, "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}]},
        {"label": "DateTime", "pattern": [{"ENT_TYPE": "DATE", "OP": "+"}, {"LEMMA": {"IN": end_befores}, "OP": "?"}, {"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}]},
        
        # Time -- Date
        {"label": "DateTime", "pattern": [{"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}, {"LEMMA": {"IN": start_befores}, "OP": "?"}, {"LEMMA": {"IN": date_words}}]},
        {"label": "DateTime", "pattern": [{"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}, {"LEMMA": {"IN": end_befores}, "OP": "?"}, {"LEMMA": {"IN": date_words}}]},
        {"label": "DateTime", "pattern": [{"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}, {"LEMMA": {"IN": start_befores}, "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "+"}]},
        {"label": "DateTime", "pattern": [{"ENT_TYPE": "TIME", "OP": "+"}, {"TEXT":{"REGEX": "[AaPp][Mm]"}}, {"LEMMA": {"IN": end_befores}, "OP": "?"}, {"ENT_TYPE": "DATE", "OP": "+"}]},
        
        # occurrences
        {"label": "occurrences", "pattern": [{"IS_DIGIT": True}, {"LOWER": "times"}]},
        {"label": "occurrences", "pattern": [{"ENT_TYPE": "CARDINAL"}, {"LOWER": "times"}]},
    ]
    ruler.add_patterns(patterns)


    clean_s = " ".join(s.lower().split()) # clean string -- lower for freqency matching -- split to remove extra spaces
    doc = nlp(clean_s)

    def round_dt(dt, delta): # Round datetime to next half-hour for defaults
        return dt + (datetime.min - dt) % delta
        
    # default values
    task = doc.text # remove substr from doc.text to get task
    start_date = round_dt(datetime.now(), timedelta(minutes=30))
    duration = 30 # default task length is 30 minutes
    occurrences = 0
    end_date = datetime.now() + timedelta(minutes=30)
    no_end_set = True # if user text doesn't specify end date
    freq_set = False # if frequency has been specified in user text

    def trans_date(s):
        s = " ".join([word for word in s.split() if word != "the"])
        cal = pdt.Calendar()
        return cal.parseDT(s, start_date)[0]

    def trans_freq(s):
        frequencies[s]()
        freq_set = True

    def trans_duration(s):
        cal = pdt.Calendar()
        return (cal.parseDT(s, start_date)[0] - start_date).total_seconds() / 60
        
    for ent in doc.ents:
        before_ent = doc.text[:ent.start_char].strip()
        if ent.label_ == "occurrences":
            occurrences = int(w2n.word_to_num(ent.text.split()[0]))
            task = task.replace(ent.text, "")
        elif ent.label_ == "DATE" or ent.label_ == "TIME" or ent.label_ == "DateTime":
            freq_list = [freq for freq in frequencies if freq in ent.text]
            end_list = [ent.start_char-len(bef)-1 for bef in end_befores if before_ent.endswith(" " + bef)]
            start_list = [ent.start_char-len(bef)-1 for bef in start_befores if before_ent.endswith(" " + bef)] 
            if freq_list:
                trans_freq(freq_list[0])
                task = task.replace(ent.text, "")
            elif ent.start_char > 0 and end_list:
                no_end_set = False
                end_date = trans_date(ent.text)
                task = task.replace(doc.text[end_list[0]:ent.end_char], "")
            elif before_ent.endswith(" for"):
                duration = trans_duration(ent.text)
                task = task.replace(doc.text[ent.start_char-4:ent.end_char], "")
            else:  
                if ent.start_char > 0 and start_list:
                    task = task.replace(doc.text[start_list[0]:ent.end_char], "")
                else:
                    task = task.replace(ent.text, "")
                start_date = trans_date(ent.text)

    for freq in frequencies:
        if freq in task: # if frequency still in task string (hasn't been found through entity naming)
            trans_freq(freq)
            task = task.replace(freq, "")

    if no_end_set:
        end_date = start_date + timedelta(minutes=30)
        if freq_set:
            end_date = date(date.today().year, 12, 31)
            
    task = task.strip()
    start_date = start_date.strftime('%c')
    end_date = end_date.strftime('%c')

    return [task,start_date,end_date,duration,occurrences,fb]
