import os
import re
import py2neo
from tqdm import tqdm
import argparse
import json


# General function to import entities
def import_entity(client, entity_type, entities, extra_properties=None):
    def create_node(client, entity_type, name, properties=None):
        properties_str = (
            ", ".join(f'{key}:"{value}"' for key, value in properties.items())
            if properties
            else ""
        )
        order = f'CREATE (n:{entity_type}{{名称:"{name}"{", " + properties_str if properties_str else ""}}})'
        client.run(order)

    print(f"Importing {entity_type} data")
    for entity in tqdm(entities):
        properties = (
            {k: entity.get(k) for k in extra_properties} if extra_properties else None
        )
        create_node(client, entity_type, entity["名称"], properties)


# Function to import relationships
def create_all_relationships(client, all_relationships):
    def create_relationship(client, entity_type1, name1, relation, entity_type2, name2):
        order = (
            f'MATCH (a:{entity_type1}{{名称:"{name1}"}}),(b:{entity_type2}{{名称:"{name2}"}}) '
            f"CREATE (a)-[r:{relation}]->(b)"
        )
        client.run(order)

    print("Importing relationships...")
    for entity_type1, name1, relation, entity_type2, name2 in tqdm(all_relationships):
        create_relationship(client, entity_type1, name1, relation, entity_type2, name2)


if __name__ == "__main__":
    # Database connection parameters
    parser = argparse.ArgumentParser(
        description="Create a knowledge graph from medical.json"
    )
    parser.add_argument(
        "--website",
        type=str,
        default="http://localhost:7474",
        help="Neo4j connection URL",
    )
    parser.add_argument("--user", type=str, default="neo4j", help="Neo4j username")
    parser.add_argument(
        "--password", type=str, default="password", help="Neo4j password"
    )
    parser.add_argument("--dbname", type=str, default="neo4j", help="Database name")
    args = parser.parse_args()

    # Connecting to the database
    client = py2neo.Graph(
        args.website, user=args.user, password=args.password, name=args.dbname
    )

    # Clear all existing entities in the database
    is_delete = input("Warning: Do you want to delete all entities in Neo4j? (y/n): ")
    if is_delete.lower() == "y":
        client.run("MATCH (n) DETACH DELETE n")

    # Read medical data from JSON file
    with open("./data/medical_new_2.json", "r", encoding="utf-8") as f:
        all_data = f.read().split("\n")

    # All entities
    all_entity = {
        "Disease": [],
        "Drug": [],
        "Food": [],
        "Checkup": [],
        "Department": [],
        "Symptom": [],
        "Treatment": [],
        "DrugCompany": [],
    }

    # Relationships between entities
    relationships = []

    for data in all_data:
        if len(data) < 3:
            continue
        data = json.loads(data[:-1])  # Use json.loads instead of eval for safety

        disease_name = data.get("name", "")
        all_entity["Disease"].append(
            {
                "名称": disease_name,
                "DiseaseIntroduction": data.get("desc", ""),
                "DiseaseCause": data.get("cause", ""),
                "PreventionMeasures": data.get("prevent", ""),
                "TreatmentDuration": data.get("cure_lasttime", ""),
                "CureProbability": data.get("cured_prob", ""),
                "SusceptiblePopulation": data.get("easy_get", ""),
            }
        )

        drugs = data.get("common_drug", []) + data.get("recommand_drug", [])
        all_entity["Drug"].extend(drugs)
        if drugs:
            relationships.extend(
                [("Disease", disease_name, "UsesDrug", "Drug", drug) for drug in drugs]
            )

        do_eat = data.get("do_eat", []) + data.get("recommand_eat", [])
        no_eat = data.get("not_eat", [])
        all_entity["Food"].extend(do_eat + no_eat)
        if do_eat:
            relationships.extend(
                [
                    ("Disease", disease_name, "RecommendedFood", "Food", f)
                    for f in do_eat
                ]
            )
        if no_eat:
            relationships.extend(
                [("Disease", disease_name, "AvoidFood", "Food", f) for f in no_eat]
            )

        check = data.get("check", [])
        all_entity["Checkup"].extend(check)
        if check:
            relationships.extend(
                [
                    ("Disease", disease_name, "RequiresCheckup", "Checkup", ch)
                    for ch in check
                ]
            )

        cure_department = data.get("cure_department", [])
        all_entity["Department"].extend(cure_department)
        if cure_department:
            relationships.append(
                (
                    "Disease",
                    disease_name,
                    "BelongsToDepartment",
                    "Department",
                    cure_department[-1],
                )
            )

        symptom = data.get("symptom", [])
        symptom = [s.rstrip("...") for s in symptom]
        all_entity["Symptom"].extend(symptom)
        if symptom:
            relationships.extend(
                [
                    ("Disease", disease_name, "HasSymptom", "Symptom", sy)
                    for sy in symptom
                ]
            )

        cure_way = data.get("cure_way", [])
        cure_way = [c[0] if isinstance(c, list) else c for c in cure_way]
        cure_way = [s for s in cure_way if len(s) >= 2]
        all_entity["Treatment"].extend(cure_way)
        relationships.extend(
            [
                ("Disease", disease_name, "TreatmentMethod", "Treatment", cure_w)
                for cure_w in cure_way
            ]
        )

        acompany_with = data.get("acompany", [])
        if acompany_with:
            relationships.extend(
                [
                    ("Disease", disease_name, "ComorbidWith", "Disease", disease)
                    for disease in acompany_with
                ]
            )

        drug_detail = data.get("drug_detail", [])
        for detail in drug_detail:
            lis = detail.split(",")
            if len(lis) != 2:
                continue
            p, d = lis[0], lis[1]
            all_entity["DrugCompany"].append(d)
            all_entity["Drug"].append(p)
            relationships.append(("DrugCompany", d, "Produces", "Drug", p))

    relationships = list(set(relationships))  # Remove duplicates
    all_entity = {
        k: (list(set(v)) if k != "Disease" else v) for k, v in all_entity.items()
    }

    # Save relationships to file
    with open("./data/rel_aug.txt", "w", encoding="utf-8") as f:
        for rel in relationships:
            f.write(" ".join(rel))
            f.write("\n")

    # Save entities to file
    if not os.path.exists("data/ent_aug"):
        os.mkdir("data/ent_aug")
    for entity_type, entities in all_entity.items():
        with open(f"data/ent_aug/{entity_type}.txt", "w", encoding="utf-8") as f:
            if entity_type != "Disease":
                for ent in entities:
                    f.write(ent + "\n")
            else:
                for ent in entities:
                    f.write(ent["名称"] + "\n")

    # Import entities and relationships into Neo4j
    for entity_type in all_entity:
        if entity_type != "Disease":
            import_entity(client, entity_type, all_entity[entity_type])
        else:
            import_entity(
                client,
                entity_type,
                all_entity[entity_type],
                extra_properties=[
                    "DiseaseIntroduction",
                    "DiseaseCause",
                    "PreventionMeasures",
                    "TreatmentDuration",
                    "CureProbability",
                    "SusceptiblePopulation",
                ],
            )

    create_all_relationships(client, relationships)
