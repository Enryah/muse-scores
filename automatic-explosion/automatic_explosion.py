import xml.etree.ElementTree as ET
import copy
import logging

logging.basicConfig(format='%(levelname)s - %(message)s', #%(asctime)s - %(name)s - 
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def explode(input_file, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()

    score = root.find("Score")
    parts = score.findall("Part")

    parts_parsed = {}
    staff_groups = {}

    for part in parts:
        staff_id = part.find("Staff").attrib["id"]
        track_name = part.find("trackName").text
        parts_parsed[staff_id] = {"trackName" : track_name}
        if track_name in staff_groups:
            staff_groups[track_name].append(staff_id)
        else:
            staff_groups[track_name] = [staff_id]

    for part_id in parts_parsed:
        parts_parsed[part_id]["staff"] = score.find("Staff[@id='{}']".format(part_id))

    empty_staff_ids = [part_id for part_id in parts_parsed if 
                   not [a for a in filter(lambda m: m.find("voice").findall("Chord"), parts_parsed[part_id]["staff"].findall("Measure"))]]

    copy_empty_staff_from = {}

    for empty_id in empty_staff_ids:
        for other_id in parts_parsed:
            if not other_id in empty_staff_ids and parts_parsed[other_id]["trackName"] == parts_parsed[empty_id]["trackName"]:
                copy_empty_staff_from[empty_id] = other_id
                break

    for empty_id in copy_empty_staff_from:
        logger.info("Found empty staff with id {}, copy from staff with id {}".format(empty_id, copy_empty_staff_from[empty_id]))

    for empty_id in copy_empty_staff_from:
        empty_staff = parts_parsed[empty_id]["staff"]
        copy_staff = parts_parsed[copy_empty_staff_from[empty_id]]["staff"]
        for m in empty_staff.findall("Measure"):
            empty_staff.remove(m)
        for m in copy_staff.findall("Measure"):
            empty_staff.append(copy.deepcopy(m))

    no_measures = len(parts_parsed["1"]["staff"].findall("Measure"))

    for staff_name in staff_groups:
        staff_ids = staff_groups[staff_name]
        for i, si in enumerate(staff_ids):
            measures = parts_parsed[si]["staff"].findall("Measure")
            for mid, measure in enumerate(measures):
                voices = measure.findall("voice")
                logger.info("Staff {}, measure {}: Found {} voice".format(si, mid, len(voices)))
                if len(voices) > 1:
                    for j in range(0, len(voices)):
                        voice = voices[j]
                        if j != i or not list(voice):
                            logger.info("Staff {}, measure {}: Remove voice {}".format(si, mid, j))
                            measure.remove(voices[j])
                if not measure.findall("voice"):
                    logger.info("Staff {}, measure {}: Add voice 0".format(si, mid))
                    measure.append(voices[0])

    tree.write(output_file)