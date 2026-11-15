
-- NYC Taxi Analytics
-- Reference table seed data

INSERT INTO vendors (vendor_id, vendor_name)
VALUES
    (1, 'Creative Mobile Technologies'),
    (2, 'VeriFone Inc.'),
    (6, 'Vendor 6 - Description Unverified'),
    (7, 'Vendor 7 - Description Unverified')
ON CONFLICT (vendor_id) DO NOTHING;

INSERT INTO payment_types (payment_type_id, description)
VALUES
    (0, 'Flex Fare trip'),
    (1, 'Credit card'),
    (2, 'Cash'),
    (3, 'No charge'),
    (4, 'Dispute'),
    (5, 'Unknown'),
    (6, 'Voided trip')
ON CONFLICT (payment_type_id) DO NOTHING;

INSERT INTO rate_codes (rate_code_id, description)
VALUES
    (1, 'Standard rate'),
    (2, 'JFK'),
    (3, 'Newark'),
    (4, 'Nassau or Westchester'),
    (5, 'Negotiated fare'),
    (6, 'Group ride'),
    (99, 'Unknown')
ON CONFLICT (rate_code_id) DO NOTHING;
