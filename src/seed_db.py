from database import driver


def seed_database():
    clear_query = "MATCH (n) DETACH DELETE n"

    seed_query = """
    // Create Clients
    CREATE (healthcorp:Client {name: 'HealthCorp UK', industry: 'Healthcare', region: 'Europe'})
    CREATE (fintech:Client {name: 'Bank X', industry: 'Finance', region: 'North America'})

    // Create Skills
    CREATE (s1:Skill {name: 'Cloud Migration'})
    CREATE (s2:Skill {name: 'Cybersecurity'})
    CREATE (s3:Skill {name: 'AWS Architecture'})
    CREATE (s4:Skill {name: 'EU Data Regulations'})

    // Create Consultants
    CREATE (alex:Consultant {name: 'Alex Rivera', role: 'Principal Architect', email: 'alex.r@firm.com', location: 'London'})
    CREATE (priya:Consultant {name: 'Priya Sharma', role: 'Senior Cloud Engineer', email: 'priya.s@firm.com', location: 'Berlin'})
    CREATE (sarah:Consultant {name: 'Sarah Chen', role: 'Security Director', email: 'sarah.c@firm.com', location: 'New York'})

    // Create Projects
    CREATE (p1:Project {
        name: 'HealthCorp Cloud Modernization', 
        description: 'Designed and deployed an AWS multi-region scalable HIPAA/GDPR compliant cloud platform for NHS-linked health platform.',
        summary: 'Cloud platform deployment for healthcare client in Europe with secure clinical data processing.'
    })
    CREATE (p2:Project {
        name: 'Bank X Zero Trust Framework', 
        description: 'Architected enterprise IAM and real-time threat detection for retail banking ops.',
        summary: 'Cybersecurity and regulatory framework implementation.'
    })

    // Relationships
    CREATE (alex)-[:HAS_SKILL]->(s1)
    CREATE (alex)-[:HAS_SKILL]->(s3)
    CREATE (alex)-[:LED_PROJECT]->(p1)

    CREATE (priya)-[:HAS_SKILL]->(s1)
    CREATE (priya)-[:HAS_SKILL]->(s4)
    CREATE (priya)-[:WORKED_ON]->(p1)

    CREATE (sarah)-[:HAS_SKILL]->(s2)
    CREATE (sarah)-[:HAS_SKILL]->(s4)
    CREATE (sarah)-[:LED_PROJECT]->(p2)

    CREATE (p1)-[:FOR_CLIENT]->(healthcorp)
    CREATE (p2)-[:FOR_CLIENT]->(fintech)

    CREATE (p1)-[:LOCATED_IN]->(healthcorp)
    """

    with driver.session() as session:
        print("Clearing database...")
        session.run(clear_query)
        print("Seeding new graph data...")
        session.run(seed_query)
        print("Database seeded successfully!")


if __name__ == "__main__":
    seed_database()