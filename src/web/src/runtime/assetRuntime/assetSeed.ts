/**
 * Asset seed — Sprint 29.3.
 * Links buildings/fleet/docs to EBN + Citizens + Life vehicles.
 */

import { EBN_HOME_PROFILE_ID, EBN_PARTNER_PROFILE_ID } from "@/runtime/businessNetwork";
import { EDC_CITIZEN_OWNER, EDC_CITIZEN_DEV, EDC_ORG_DEMO } from "@/runtime/digitalCitizen";
import { assetRegistry } from "./assetRegistry";

export function seedAssets() {
  if (assetRegistry.get("ast_hq_hub")) return;

  assetRegistry.create({
    id: "ast_hq_hub",
    type: "headquarters",
    profile: { name: "Demo Corp HQ", description: "Hub Plaza headquarters", tags: ["city", "hub"] },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "building", buildingId: "hub", districtId: "enterprise", x: 48, y: 42, label: "Hub Plaza" },
    status: "in_use",
    metadata: { cityBuilding: "hub", orgId: EDC_ORG_DEMO },
  });
  assetRegistry.setLifecycle("ast_hq_hub", "in_use");

  assetRegistry.create({
    id: "ast_office_dev",
    type: "office",
    profile: { name: "Engineering Wing", tags: ["office"] },
    ownership: { kind: "department", companyId: EBN_HOME_PROFILE_ID, departmentId: "dept_eng" },
    location: { kind: "building", buildingId: "developer", districtId: "developer", x: 62, y: 55 },
    status: "in_use",
  });
  assetRegistry.setLifecycle("ast_office_dev", "in_use");

  assetRegistry.create({
    id: "ast_wh_1",
    type: "warehouse",
    profile: { name: "Central Warehouse", tags: ["logistics"] },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "warehouse", warehouseId: "wh_central", buildingId: "erp", districtId: "erp" },
    status: "in_use",
  });
  assetRegistry.setLifecycle("ast_wh_1", "in_use");

  assetRegistry.create({
    id: "ast_van_1",
    type: "vehicle",
    profile: { name: "Fleet Van 1", serialNumber: "VAN-001", tags: ["fleet"] },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "building", buildingId: "hub", vehicleId: "veh_van_1" },
    status: "registered",
    metadata: { lifeVehicleId: "veh_van_1" },
  });
  assetRegistry.setLifecycle("ast_van_1", "registered");

  assetRegistry.create({
    id: "ast_drone_1",
    type: "drone",
    profile: { name: "Survey Drone A1", manufacturer: "ADOS Air" },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "building", buildingId: "production", districtId: "production" },
    status: "registered",
  });

  assetRegistry.create({
    id: "ast_laptop_dev",
    type: "computer",
    profile: { name: "Dev Workstation", serialNumber: "WS-DEV-12" },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "citizen", citizenId: EDC_CITIZEN_DEV, buildingId: "ai_studio" },
    status: "assigned",
  });
  assetRegistry.setLifecycle("ast_laptop_dev", "assigned");
  assetRegistry.update("ast_laptop_dev", {
    assignedCitizenId: EDC_CITIZEN_DEV,
    available: false,
  });

  assetRegistry.create({
    id: "ast_server_1",
    type: "server",
    profile: { name: "Edge Node 1", tags: ["infra"] },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "building", buildingId: "developer", districtId: "developer" },
    status: "in_use",
  });
  assetRegistry.setLifecycle("ast_server_1", "in_use");

  assetRegistry.create({
    id: "ast_msa_doc",
    type: "document",
    profile: { name: "MSA 2026 Northwind", tags: ["contract"] },
    ownership: {
      kind: "shared",
      companyId: EBN_HOME_PROFILE_ID,
      partnerCompanyId: EBN_PARTNER_PROFILE_ID,
      sharePct: 50,
      coOwners: [
        { companyId: EBN_HOME_PROFILE_ID, sharePct: 50 },
        { companyId: EBN_PARTNER_PROFILE_ID, sharePct: 50 },
      ],
    },
    location: { kind: "virtual", label: "Document vault" },
    status: "registered",
    metadata: { documentRef: "doc://contracts/msa-2026-northwind" },
  });

  assetRegistry.create({
    id: "ast_brand",
    type: "brand",
    profile: { name: "ADOS Brand Kit", tags: ["ip"] },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "virtual", label: "Brand vault" },
    status: "in_use",
  });

  assetRegistry.create({
    id: "ast_license_iso",
    type: "license",
    profile: { name: "ISO Process License", tags: ["compliance"] },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "virtual" },
    status: "registered",
  });

  assetRegistry.create({
    id: "ast_cert_iso",
    type: "certificate",
    profile: { name: "ISO 9001 Certificate" },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "virtual" },
    status: "registered",
  });

  assetRegistry.create({
    id: "ast_ai_exec",
    type: "ai_model",
    profile: { name: "Executive AI Model", tags: ["ai"] },
    ownership: { kind: "citizen", citizenId: EDC_CITIZEN_OWNER, companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "virtual", buildingId: "ai_studio", districtId: "ai" },
    status: "assigned",
  });
  assetRegistry.update("ast_ai_exec", { assignedCitizenId: EDC_CITIZEN_OWNER, available: false });
  assetRegistry.setLifecycle("ast_ai_exec", "assigned");

  assetRegistry.create({
    id: "ast_knowledge_1",
    type: "knowledge_asset",
    profile: { name: "Platform Playbooks", tags: ["knowledge"] },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "building", buildingId: "knowledge", districtId: "knowledge" },
    status: "in_use",
  });

  assetRegistry.create({
    id: "ast_digital_pack",
    type: "digital_product",
    profile: { name: "Partner Onboarding Pack", valueEstimate: 1200, currency: "USD" },
    ownership: { kind: "company", companyId: EBN_HOME_PROFILE_ID },
    location: { kind: "virtual", buildingId: "marketplace", districtId: "marketplace" },
    status: "registered",
  });

  assetRegistry.create({
    id: "ast_exc_lease",
    type: "machine",
    profile: { name: "Excavator X200", manufacturer: "BuildCo" },
    ownership: {
      kind: "lease",
      companyId: EBN_HOME_PROFILE_ID,
      partnerCompanyId: EBN_PARTNER_PROFILE_ID,
      leaseEndsAt: new Date(Date.now() + 90 * 86400_000).toISOString(),
    },
    location: { kind: "building", buildingId: "erp", districtId: "erp" },
    status: "in_use",
  });
  assetRegistry.setLifecycle("ast_exc_lease", "in_use");
}
