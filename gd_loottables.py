import os


root_base = r"C:\Program Files (x86)\Steam\steamapps\common\Grim Dawn\database\records"

root1 = r"\creatures\enemies"
root2 = r"\items\loottables\mastertables"

prefix = r"C:\Program Files (x86)\Steam\steamapps\common\Grim Dawn\database"

item_fn = r"C:\Program Files (x86)\Steam\steamapps\common\Grim Dawn\resources\text_en\tags_items.txt"
quest_fn = r"C:\Program Files (x86)\Steam\steamapps\common\Grim Dawn\resources\text_en\tags_storyelements.txt"
enemy_fn = r"C:\Program Files (x86)\Steam\steamapps\common\Grim Dawn\resources\text_en\tags_creatures.txt"

enemies = []

enemy_names = {}
item_names = {}

mastertables = {}

debug = False

#common, rare, epic, legendary
tiers = {1: False, 2: False, 3: False, 4: False}

def get_quality(line):
    if "_a0" in line or "_a1" in line:
        return tiers[1]
    if "_b0" in line or "_b1" in line:
        return tiers[2]
    if "_c0" in line or "_c1" in line:
        return tiers[3]
    if "_d0" in line or "_d1" in line:
        return tiers[4]
    return False
    
def get_output():
    res = "loottable_output"
    
    if tiers[1]:
        res += "_Common"
    if tiers[2]:
        res += "_Rare"
    if tiers[3]:
        res += "_Epic"
    if tiers[4]:
        res += "_Legendary"
    return res + ".txt"

#utility function
def before(value, a):
    pos_a = value.find(a)
    return "" if pos_a == -1 else value[0:pos_a]

#utility function
def after(value, a):
    pos_a = value.find(a)
    return "" if pos_a == -1 else "" if len(value) <= pos_a + len(a) else value[pos_a:]

#utility function
def get_name_for_item(record):
    f = open(prefix + "\\" + record)
    style = ""
    name = ""
    for line in f:
        if "tag" in line and ",," not in line:
            split = line.rsplit(",")
            if split[1] in item_names:
                if "Style" in line:
                    style = item_names[split[1]]
                elif "Quality" in line:
                    style = item_names[split[1]]
                elif "Name" in line:
                    name = item_names[split[1]]
    return (style + " " + name).strip()

#called at bottom of chain; if a tdyn has multiple of the same item at different weights, uses the lowest weight
#called after handle_tdyn
def normalize_tdyn(loot):
    norm = {}
    seen_names = []
    seen_keys = []
    for key in loot:
        if loot[key]["name"] not in seen_names:
            norm[key] = loot[key]
            seen_names.append(loot[key]["name"])
            seen_keys.append(key)
        else:
            idx = seen_names.index(loot[key]["name"])
            k = seen_keys[idx]
            norm[k]["weight"] = loot[key]["weight"]
    return norm

#called after handle_lt
def build_tdyn(tdyn):
    f = open(prefix + "\\" + tdyn)
    loot = {}
    for line in f:
        if "lootName" in line and ",," not in line:
            split = line.rsplit(",")
            name = get_name_for_item(split[1])
            loot[split[0]] = {"name": name, "weight": 0}
        elif "lootWeight" in line and ",," not in line and ",0," not in line:
            split = line.rsplit(",")
            loot["lootName" + split[0].rsplit("Weight")[1]]["weight"] = float(split[1])
    
    return normalize_tdyn(loot)

#called after handle_master
def handle_lt(lt):
    f = open(prefix + "\\" + lt)
    
    for line in f:
        if "records" in line and ",," not in line:
            split1 = line.rsplit(",")
            split2 = split1[1].rsplit(";")
            if "tdyn" in split2[len(split2) - 1]:
                return build_tdyn(split2[len(split2) - 1])

#builds the data of a mastertable
def build_master(master):
    f = open(prefix + "\\" + master)
    loottable = {}
    for line in f:
        if "lootName" in line and ",," not in line:
            split = line.rsplit(",")
            loottable[split[0]] = {"loot": split[1], "weight": 0}
        elif "lootWeight" in line and ",0," not in line:
            split = line.rsplit(",")
            loottable["lootName" + split[0][10:]]["weight"] = float(split[1])
    for key in loottable:
        loottable[key]["loot"] = handle_lt(loottable[key]["loot"])
    return loottable
    
def handle_tdyn(inpt, chance):
    tdyn = build_tdyn(inpt)
    res = []
    if len(tdyn) == 1:
        for key in tdyn:
            res.append("\t" + tdyn[key]["name"] + " - " + chance + "%")
    else:
        sum1 = 0
        for key in tdyn:
            sum1 += tdyn[key]["weight"]
        for key in tdyn:
            res.append("\t" + tdyn[key]["name"] + " - " + str(float(chance) * (tdyn[key]["weight"])/sum1) + "%")
    return res
    
def handle_master(mt, chance):
    master = mastertables[mt]
    sum1 = 0.0
    res = []
    res.append("From " + mt + " with " + chance + "% chance to use")
    for key in master:
        sum1 += float(master[key]["weight"])
    for key in master:
        master[key]["weight"] = float(master[key]["weight"])/sum1
        weight1 = float(master[key]["weight"])
        sum2 = 0.0
        sub = master[key]["loot"]
        for key2 in sub:
            sum2 += float(sub[key2]["weight"])
        for key2 in sub:
            sub[key2]["weight"] = float(sub[key2]["weight"])/sum2
            sub[key2]["weight"] = float(sub[key2]["weight"])*(weight1*float(chance))
    for key in master:
        for key2 in master[key]["loot"]:
            res.append("\t" + master[key]["loot"][key2]["name"] + " - " + str(master[key]["loot"][key2]["weight"]) + "%")
    return res

def handle_enemy(enemy):
    f = open(enemy)
    changed = False
    name = ""
    ddict = {
            "chanceToEquipHead": {"chance": 0},
            "chanceToEquipChest": {"chance": 0},
            "chanceToEquipShoulders": {"chance": 0},
            "chanceToEquipHands": {"chance": 0},
            "chanceToEquipLegs": {"chance": 0},
            "chanceToEquipFeet": {"chance": 0},
            "chanceToEquipRightHand": {"chance": 0},
            "chanceToEquipLeftHand": {"chance": 0},
            "chanceToEquipFinger1": {"chance": 0},
            "chanceToEquipFinger2": {"chance": 0},
            "chanceToEquipMisc1": {"chance": 0},
            "chanceToEquipMisc2": {"chance": 0},
            "chanceToEquipMisc3": {"chance": 0}
             }
             
    for line in f:
        if "chanceToEquip" in line and not ",0.000000," in line and not "Item" in line:
            changed = True
            split = line.rsplit(",")
            ddict[split[0]]["chance"] = float(split[1])/100.0
        elif "chanceToEquip" in line and "Item" in line and not ",0," in line:
            split = line.rsplit(",")
            ddict[before(split[0], "Item")][after(split[0], "Item")] = int(split[1])
        elif "loot" in line and "Item" in line and ",," not in line:
            split = line.rsplit(",")
            ddict["chanceToEquip" + before(split[0][4:], "Item")]["loot" + after(split[0], "Item")] = split[1]
        elif "description," in line and ",," not in line:
            try:
                name = enemy_names[line.rsplit(",")[1]]
            except KeyError as e:
                if debug:
                    print("Unknown tag - " + str(e))
    
    if changed:
        output = []
        output.append(name + "\n")
        for key in ddict:
            if ddict[key]["chance"] != 0:
                if len(ddict[key]) > 3:
                    sum = 0
                    for entry in ddict[key]:
                        if "Item" in entry and "loot" not in entry:
                            sum += ddict[key][entry]
                    for entry in ddict[key]:
                        if "Item" in entry and "loot" not in entry:
                            ddict[key][entry] = 100.0*ddict[key]["chance"]*float(ddict[key][entry])/sum
                            try:
                                output.append(ddict[key]["lootItem" + str(after(entry, "Item")[4:])] + " - " + str(ddict[key][entry]) + "%\n")
                            except KeyError as e:
                                if debug:
                                    print("Error with " + after(enemy, "database") + " - " + str(e))
                                else:
                                    continue
        return output
    else:
        return []

def handle_direct(record):
    f = open(prefix + "\\" + record)
    
    for line in f:
        if "tag" in line and "Desc" not in line and ",," not in line:
            tag = line.split(",")
            if tag[1] in item_names:
                return item_names[tag[1]]
    
    return ""

def main():
    for line in open(enemy_fn):
        if "=" in line:
            string = line.rsplit("=")
            enemy_names[string[0]] = string[1]
    for line in open(item_fn):
        if "=" in line:
            string = line.rsplit("=")
            item_names[string[0]] = before(string[1], "\n")
    for line in open(quest_fn):
        if "=" in line:
            string = line.rsplit("=")
            item_names[string[0]] = before(string[1], "\n")
    for path, subdirs, files in os.walk(root_base + root1):
        for name in files:
            if r"creatures\enemies\bios" not in path and r"\creatures\enemies\anm" not in path:
                enemies.append(os.path.join(path, name))
    for path, subdirs, files in os.walk(root_base + root2):
        for name in files:
            mastertables[name] = build_master("/records" + root2 + "\\" + name)
    with open(get_output(), 'w') as out:
        for enemy in enemies:
            res = ""
            lines = False
            for line in handle_enemy(enemy):
                chance = 0.0
                if "mt_hu_" in line or "crafting_blueprints" in line:
                    continue
                if " - " in line:
                    chance = after(line, " - ").rsplit("%")[0][3:]
                if "mastertables" in line:
                    quality = get_quality(line)
                    if quality:
                        lines = True
                        prior = before(line, " - ").rsplit("/")
                        for line in handle_master(prior[len(prior) - 1], chance):
                            res += line + "\n"
                elif "tdyn" in line:
                    quality = get_quality(line)
                    if quality:
                        lines = True
                        for line in handle_tdyn(before(line, " - "), chance):
                            res += line + "\n"
                elif " - " in line:
                    lines = True
                    split = line.rsplit(" - ")
                    res += "\t" + handle_direct(split[0]) + " - " + split[1]
                else:
                    res += line.strip() + "\n"
            if lines:
                out.write(res + "\n")
        out.close()
        
if __name__ == '__main__':
    main()
