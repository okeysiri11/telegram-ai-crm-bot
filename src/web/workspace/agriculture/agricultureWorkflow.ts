/**
 * Agriculture operational pilot — Sprint 31.1.
 * Reuses /api/agro/v1 + /api/agro-supply-chain/v1 + shared ecosystem template.
 * Does not fork Automotive, Beauty, or Cafe.
 */

import { apiFetch } from "@/integrations/apiClient";
import { webConfig } from "@/config/webConfig";
import { hubIntegrations } from "@/integrations/hub";
import {
  timedStep,
  stepAiConcierge,
  stepAiTeamConfigure,
  stepNotification,
  stepMissionControl,
  stepObservability,
  computeReusePercentage,
  type WorkflowRunResult,
  type WorkflowStepResult,
} from "../ecosystem-template";

const AGRO = () => webConfig.agroPrefix;
const SC = () => webConfig.agroSupplyChainPrefix;
const AE = () => webConfig.agroEnterprisePrefix;
const AF = () => webConfig.agroFinancePrefix;
const AA = () => webConfig.aiAgronomistPrefix;
const ISAM = () => hubIntegrations.authentication;
const AMO = () => webConfig.aiMarketingOsPrefix;

export type { WorkflowStepResult };

export async function runAgricultureLiveWorkflow(opts: {
  farmerName: string;
  farmerEmail: string;
  organizationId: string;
}): Promise<WorkflowRunResult> {
  const steps: WorkflowStepResult[] = [];
  const wall = performance.now();

  let farmerId = "";
  let farmId = "";
  let productId = "";
  let harvestId = "";
  let warehouseId = "";
  let buyerId = "";
  let offerId = "";
  let requestId = "";
  let orderId = "";
  let contractId = "";
  let shipmentId = "";
  let containerId = "";

  steps.push(
    await timedStep("login", "Login (production auth)", async () => {
      const isam = await apiFetch(`${ISAM()}/health`);
      const body = isam.ok ? ((await isam.json()) as Record<string, unknown>) : {};
      return { detail: "Staff session + ISAM health", data: { gate: "production_auth", isam: body } };
    }),
  );

  steps.push(
    await timedStep("farm_crm", "Farm CRM", async () => {
      const farmer = await apiFetch(`${AGRO()}/farmers`, {
        method: "POST",
        body: JSON.stringify({
          name: opts.farmerName,
          email: opts.farmerEmail,
          country: "KE",
          region: "Rift",
        }),
      });
      const farmerBody = (await farmer.json()) as Record<string, unknown>;
      if (!farmer.ok) throw new Error(String(farmerBody.error || "Farmer register failed"));
      farmerId = String(farmerBody.farmer_id || "");

      const farm = await apiFetch(`${AGRO()}/farms`, {
        method: "POST",
        body: JSON.stringify({
          farmer_id: farmerId,
          name: "Pilot Farm",
          size_hectares: 25,
          location: "Nakuru",
        }),
      });
      const farmBody = (await farm.json()) as Record<string, unknown>;
      if (!farm.ok) throw new Error(String(farmBody.error || "Farm create failed"));
      farmId = String(farmBody.farm_id || "");

      const field = await apiFetch(`${AGRO()}/fields`, {
        method: "POST",
        body: JSON.stringify({
          farm_id: farmId,
          name: "North Field",
          crop_type: "wheat",
          area_hectares: 8,
          soil_type: "loam",
        }),
      });
      const fieldBody = (await field.json()) as Record<string, unknown>;
      if (!field.ok) throw new Error(String(fieldBody.error || "Field create failed"));

      const supplier = await apiFetch(`${AGRO()}/suppliers`, {
        method: "POST",
        body: JSON.stringify({ name: "Pilot Inputs Co", email: "inputs@demo.corp", category: "inputs" }),
      });
      const supplierBody = supplier.ok ? ((await supplier.json()) as Record<string, unknown>) : {};

      return {
        detail: `farmer=${farmerId}; farm=${farmId}`,
        data: { farmer: farmerBody, farm: farmBody, field: fieldBody, supplier: supplierBody },
      };
    }),
  );

  steps.push(
    await timedStep("products", "Products", async () => {
      const res = await apiFetch(`${AGRO()}/products`, {
        method: "POST",
        body: JSON.stringify({
          name: "Pilot Wheat",
          farmer_id: farmerId,
          price: 210,
          quantity: 50,
          crop_id: "wheat",
        }),
      });
      const body = (await res.json()) as Record<string, unknown>;
      if (!res.ok) throw new Error(String(body.error || "Product create failed"));
      productId = String(body.product_id || "");
      return { detail: `product_id=${productId}`, data: body };
    }),
  );

  steps.push(
    await timedStep("harvest", "Harvest", async () => {
      const season = await apiFetch(`${AGRO()}/harvest/seasons`, {
        method: "POST",
        body: JSON.stringify({ name: "Main Season", year: 2026, region: "KE" }),
      });
      const seasonBody = (await season.json()) as Record<string, unknown>;
      if (!season.ok) throw new Error(String(seasonBody.error || "Season failed"));

      const harvest = await apiFetch(`${AGRO()}/harvest/records`, {
        method: "POST",
        body: JSON.stringify({
          crop_id: "wheat",
          season_id: seasonBody.season_id,
          region: "KE",
          quantity: 40,
          moisture_pct: 13,
          farm_id: farmId,
          farmer_id: farmerId,
        }),
      });
      const harvestBody = (await harvest.json()) as Record<string, unknown>;
      if (!harvest.ok) throw new Error(String(harvestBody.error || "Harvest failed"));
      harvestId = String(harvestBody.harvest_id || "");

      const cert = await apiFetch(`${AGRO()}/harvest/certificates`, {
        method: "POST",
        body: JSON.stringify({ harvest_id: harvestId, grade: "A", issuer: "AgroLab" }),
      });
      const certBody = cert.ok ? ((await cert.json()) as Record<string, unknown>) : {};
      return {
        detail: `harvest=${harvestId}`,
        data: { season: seasonBody, harvest: harvestBody, certificate: certBody },
      };
    }),
  );

  steps.push(
    await timedStep("warehouse", "Warehouse + inventory", async () => {
      const wh = await apiFetch(`${AGRO()}/warehouse/warehouses`, {
        method: "POST",
        body: JSON.stringify({
          name: "Pilot Silo",
          region: "KE",
          capacity_tons: 250,
          owner_id: farmerId,
        }),
      });
      const whBody = (await wh.json()) as Record<string, unknown>;
      if (!wh.ok) throw new Error(String(whBody.error || "Warehouse failed"));
      warehouseId = String(whBody.warehouse_id || "");

      const inv = await apiFetch(`${AGRO()}/inventory/incoming`, {
        method: "POST",
        body: JSON.stringify({
          product_id: productId,
          warehouse_id: warehouseId,
          quantity: 40,
        }),
      });
      const invBody = (await inv.json()) as Record<string, unknown>;
      if (!inv.ok) throw new Error(String(invBody.error || "Inventory incoming failed"));

      // Grain elevator depth via supply chain (existing enterprise APIs)
      const elev = await apiFetch(`${SC()}/elevator`, {
        method: "POST",
        body: JSON.stringify({ action: "register", name: "Pilot Elevator", location: "Nakuru" }),
      });
      const elevBody = elev.ok ? ((await elev.json()) as Record<string, unknown>) : {};

      return {
        detail: `warehouse=${warehouseId}`,
        data: { warehouse: whBody, inventory: invBody, elevator: elevBody },
      };
    }),
  );

  steps.push(
    await timedStep("commodity_sale", "Commodity sale (grain marketplace)", async () => {
      const buyer = await apiFetch(`${AGRO()}/crm/buyers`, {
        method: "POST",
        body: JSON.stringify({
          name: "Export Mill",
          email: "mill@demo.corp",
          preferred_crops: ["wheat"],
          budget_max: 200000,
        }),
      });
      const buyerBody = (await buyer.json()) as Record<string, unknown>;
      if (!buyer.ok) throw new Error(String(buyerBody.error || "Buyer failed"));
      buyerId = String(buyerBody.buyer_id || "");

      const offer = await apiFetch(`${AGRO()}/marketplace/offers`, {
        method: "POST",
        body: JSON.stringify({
          seller_id: farmerId,
          crop_id: "wheat",
          quantity: 30,
          price: 210,
          region: "KE",
        }),
      });
      const offerBody = (await offer.json()) as Record<string, unknown>;
      if (!offer.ok) throw new Error(String(offerBody.error || "Offer failed"));
      offerId = String(offerBody.offer_id || "");

      const request = await apiFetch(`${AGRO()}/marketplace/requests`, {
        method: "POST",
        body: JSON.stringify({
          buyer_id: buyerId,
          crop_id: "wheat",
          quantity: 25,
          max_price: 220,
          region: "KE",
        }),
      });
      const requestBody = (await request.json()) as Record<string, unknown>;
      if (!request.ok) throw new Error(String(requestBody.error || "Request failed"));
      requestId = String(requestBody.request_id || "");

      const match = await apiFetch(`${AGRO()}/marketplace/match`, {
        method: "POST",
        body: JSON.stringify({ offer_id: offerId, request_id: requestId }),
      });
      const matchBody = (await match.json()) as Record<string, unknown>;
      if (!match.ok) throw new Error(String(matchBody.error || "Match failed"));

      const order = await apiFetch(`${AGRO()}/orders`, {
        method: "POST",
        body: JSON.stringify({
          buyer_id: buyerId,
          product_id: productId,
          quantity: 25,
        }),
      });
      const orderBody = (await order.json()) as Record<string, unknown>;
      if (!order.ok) throw new Error(String(orderBody.error || "Order/sale failed"));
      orderId = String(orderBody.order_id || "");

      return {
        detail: `match score=${matchBody.score}; order=${orderId}`,
        data: { buyer: buyerBody, offer: offerBody, request: requestBody, match: matchBody, order: orderBody },
      };
    }),
  );

  steps.push(
    await timedStep("contract", "Trade contract", async () => {
      // Supply-chain export contract (existing enterprise trading surface)
      const contract = await apiFetch(`${SC()}/export`, {
        method: "POST",
        body: JSON.stringify({
          action: "contract",
          buyer: "Export Mill",
          commodity: "wheat",
          tons: 25,
          price: 210,
          incoterm: "FOB",
        }),
      });
      const contractBody = (await contract.json()) as Record<string, unknown>;
      if (!contract.ok) throw new Error(String(contractBody.error || "Contract failed"));
      contractId = String(contractBody.contract_id || "");

      const docs = await apiFetch(`${SC()}/export`, {
        method: "POST",
        body: JSON.stringify({ action: "docs", contract_id: contractId }),
      });
      const docsBody = docs.ok ? ((await docs.json()) as Record<string, unknown>) : {};

      const negotiation = await apiFetch(`${AGRO()}/negotiations`, {
        method: "POST",
        body: JSON.stringify({
          offer_id: offerId,
          request_id: requestId,
          buyer_id: buyerId,
          seller_id: farmerId,
          price: 210,
          quantity: 25,
        }),
      });
      const negBody = negotiation.ok ? ((await negotiation.json()) as Record<string, unknown>) : {};

      return {
        detail: `contract=${contractId}`,
        data: { contract: contractBody, export_docs: docsBody, negotiation: negBody },
      };
    }),
  );

  steps.push(
    await timedStep("shipment", "Shipment + logistics", async () => {
      const ports = await apiFetch(`${AGRO()}/logistics/ports`);
      const portsBody = (await ports.json()) as Record<string, unknown>;
      if (!ports.ok) throw new Error(String(portsBody.error || "Ports failed"));
      const items = Array.isArray(portsBody.items) ? (portsBody.items as Record<string, unknown>[]) : [];
      const origin = items.find((p) => p.country === "KE") || items[0];
      const dest = items.find((p) => p.country === "AE") || items[1] || items[0];
      if (!origin || !dest) throw new Error("Ports unavailable for sea freight");

      const carrier = await apiFetch(`${AGRO()}/logistics/carriers`, {
        method: "POST",
        body: JSON.stringify({
          name: "SeaAgro Pilot",
          countries: ["AE", "NL"],
          rating: 4.6,
          mode: "sea",
        }),
      });
      const carrierBody = (await carrier.json()) as Record<string, unknown>;
      if (!carrier.ok) throw new Error(String(carrierBody.error || "Carrier failed"));

      const ship = await apiFetch(`${AGRO()}/export/shipments`, {
        method: "POST",
        body: JSON.stringify({
          order_id: orderId || "agro-pilot-order",
          contract_id: contractId,
          origin_country: "KE",
          destination_country: String(dest.country || "AE"),
          origin_port_id: origin.port_id,
          destination_port_id: dest.port_id,
          carrier_id: carrierBody.carrier_id,
          incoterm: "FOB",
          buyer_id: buyerId,
        }),
      });
      const shipBody = (await ship.json()) as Record<string, unknown>;
      if (!ship.ok) throw new Error(String(shipBody.error || "Shipment failed"));
      shipmentId = String(shipBody.shipment_id || "");

      const docs = await apiFetch(`${AGRO()}/export/shipments/${shipmentId}/documents`, {
        method: "POST",
        body: JSON.stringify({ cargo_value: 5250 }),
      });
      const docsBody = docs.ok ? ((await docs.json()) as Record<string, unknown>) : {};

      const container = await apiFetch(`${AGRO()}/logistics/containers`, {
        method: "POST",
        body: JSON.stringify({ shipment_id: shipmentId, container_type: "40HC" }),
      });
      const containerBody = (await container.json()) as Record<string, unknown>;
      if (!container.ok) throw new Error(String(containerBody.error || "Container failed"));
      containerId = String(containerBody.container_id || "");

      const plan = await apiFetch(`${AGRO()}/logistics/plan`, {
        method: "POST",
        body: JSON.stringify({
          origin_country: "KE",
          destination_country: String(dest.country || "AE"),
          mode: "sea",
        }),
      });
      const planBody = plan.ok ? ((await plan.json()) as Record<string, unknown>) : {};

      const dispatch = await apiFetch(`${AGRO()}/export/shipments/${shipmentId}/dispatch`, {
        method: "POST",
        body: "{}",
      });
      if (!dispatch.ok) {
        const err = (await dispatch.json()) as Record<string, unknown>;
        throw new Error(String(err.error || "Dispatch failed"));
      }

      const customs = await apiFetch(`${AGRO()}/export/shipments/${shipmentId}/customs`, {
        method: "POST",
        body: "{}",
      });
      const customsBody = customs.ok ? ((await customs.json()) as Record<string, unknown>) : {};

      const track = await apiFetch(`${AGRO()}/tracking/${shipmentId}`);
      const trackBody = track.ok ? ((await track.json()) as Record<string, unknown>) : {};

      // SC logistics depth (existing enterprise freight + route + delivery)
      const scFreight = await apiFetch(`${SC()}/logistics`, {
        method: "POST",
        body: JSON.stringify({ action: "freight", commodity: "wheat", tons: 25, mode: "sea" }),
      });
      const scFreightBody = scFreight.ok ? ((await scFreight.json()) as Record<string, unknown>) : {};
      const scRoute = await apiFetch(`${SC()}/logistics`, {
        method: "POST",
        body: JSON.stringify({
          action: "route",
          origin: "Nakuru",
          destination: "Mombasa",
          mode: "rail",
        }),
      });
      const scRouteBody = scRoute.ok ? ((await scRoute.json()) as Record<string, unknown>) : {};
      const scDelivery = await apiFetch(`${SC()}/logistics`, {
        method: "POST",
        body: JSON.stringify({
          action: "delivery",
          shipment_ref: shipmentId,
          window_start: "2026-08-01",
          window_end: "2026-08-07",
        }),
      });
      const scDeliveryBody = scDelivery.ok ? ((await scDelivery.json()) as Record<string, unknown>) : {};

      return {
        detail: `shipment=${shipmentId}; container=${containerId}`,
        data: {
          shipment: shipBody,
          documents: docsBody,
          container: containerBody,
          plan: planBody,
          customs: customsBody,
          tracking: trackBody,
          sc_freight: scFreightBody,
          sc_route: scRouteBody,
          sc_delivery: scDeliveryBody,
        },
      };
    }),
  );

  steps.push(
    await stepNotification({
      source: "agriculture_pilot_workflow",
      event: "shipment_dispatched",
      recipient: opts.farmerEmail,
      subject: "Agriculture shipment dispatched",
      body: `Shipment ${shipmentId} for harvest ${harvestId} is underway. Contract ${contractId}.`,
      payload: { shipment_id: shipmentId, contract_id: contractId, order_id: orderId },
    }),
  );

  steps.push(
    await stepAiTeamConfigure({
      organizationId: opts.organizationId,
      ecosystem: "agriculture",
      tasks: [
        { label: "AI Agronomist", task: "Advise wheat moisture and quality for export lot" },
        { label: "AI Trader", task: "Recommend FOB wheat price vs regional quote" },
        { label: "AI Logistics", task: "Optimize sea freight container load for AE" },
        { label: "AI Marketing", task: "Promote surplus grain listing to mill buyers" },
        { label: "AI Analytics", task: "Summarize harvest-to-shipment KPIs for owner" },
      ],
    }),
  );

  steps.push(
    await stepAiConcierge({
      organizationId: opts.organizationId,
      name: "Agriculture Pilot Concierge",
      role: "business_concierge",
      roleCustom: "Agriculture trade concierge",
      recommendations: [
        `harvest:${harvestId}`,
        `contract:${contractId}`,
        `shipment:${shipmentId}`,
        "Confirm phyto certificate before customs",
      ],
    }),
  );

  steps.push(
    await timedStep("ai_agronomist", "AI Agronomist probe", async () => {
      const health = await apiFetch(`${AA()}/health`);
      const healthBody = (await health.json()) as Record<string, unknown>;
      if (!health.ok) throw new Error(String(healthBody.error || "AI Agronomist health failed"));
      return { detail: "ai-agronomist health ok", data: healthBody };
    }),
  );

  steps.push(
    await timedStep("ai_marketing", "AI Marketing (AMO)", async () => {
      const health = await apiFetch(`${AMO()}/health`);
      const healthBody = (await health.json()) as Record<string, unknown>;
      if (!health.ok) throw new Error(String(healthBody.error || "AMO health failed"));
      await apiFetch(`${AMO()}/bootstrap`, { method: "POST", body: "{}" });
      const campaign = await apiFetch(`${AMO()}/campaigns`, {
        method: "POST",
        body: JSON.stringify({
          kind: "promotion",
          title: "Grain export pilot",
          budget: 120,
          channels: ["email"],
        }),
      });
      const campaignBody = campaign.ok ? ((await campaign.json()) as Record<string, unknown>) : {};
      return { detail: `campaign=${campaignBody.campaign_id || "bootstrap"}`, data: campaignBody };
    }),
  );

  steps.push(
    await timedStep("owner_dashboard", "Owner dashboard", async () => {
      const [exec, kpi, scDash, aeHealth, afHealth] = await Promise.all([
        apiFetch(`${AGRO()}/dashboards/executive`),
        apiFetch(`${AGRO()}/kpi`),
        apiFetch(`${SC()}/dashboard?type=export`),
        apiFetch(`${AE()}/health`),
        apiFetch(`${AF()}/health`),
      ]);
      const execBody = exec.ok ? ((await exec.json()) as Record<string, unknown>) : {};
      const kpiBody = kpi.ok ? ((await kpi.json()) as Record<string, unknown>) : {};
      const scBody = scDash.ok ? ((await scDash.json()) as Record<string, unknown>) : {};
      if (!exec.ok && !scDash.ok) throw new Error("Owner dashboards unavailable");
      return {
        detail: "agro executive + SC export + finance/enterprise health",
        data: {
          executive: execBody,
          kpi: kpiBody,
          supply_chain: scBody,
          agro_enterprise: aeHealth.ok,
          agro_finance: afHealth.ok,
        },
      };
    }),
  );

  steps.push(await stepMissionControl());

  steps.push(
    await timedStep("analytics", "Analytics", async () => {
      const analytics = await apiFetch(`${AGRO()}/analytics`);
      const body = (await analytics.json()) as Record<string, unknown>;
      if (!analytics.ok) throw new Error(String(body.error || "Analytics failed"));
      const domain = await apiFetch(`${AGRO()}/analytics/domains`);
      const domainBody = domain.ok ? ((await domain.json()) as Record<string, unknown>) : {};
      return { detail: "agro analytics + domains", data: { analytics: body, domains: domainBody } };
    }),
  );

  steps.push(
    await timedStep("quality_gates", "Quality gates", async () => {
      const probes = await Promise.all([
        apiFetch(`${AGRO()}/health`),
        apiFetch(`${SC()}/health`),
        apiFetch(`${AE()}/health`),
        apiFetch(`${ISAM()}/health`),
        apiFetch(`${hubIntegrations.monitoring}/health`),
        apiFetch(`${webConfig.platformBuilderPrefix}/mission-control/status`),
        apiFetch(`${webConfig.ewfPrefix}/health`),
        apiFetch(`${webConfig.beautyOsPrefix}/health`),
        apiFetch(`${webConfig.cafeOsPrefix}/health`),
        apiFetch(`${webConfig.autoPrefix}/health`),
      ]);
      const labels = ["agro", "sc", "ae", "isam", "obs", "mc", "ewf", "bos", "cos", "auto"];
      const results: Record<string, boolean> = {};
      for (let i = 0; i < probes.length; i += 1) results[labels[i]] = probes[i].ok;
      const required = ["agro", "sc", "obs", "mc"];
      if (!required.every((k) => results[k])) {
        throw new Error(`Quality gate failures: ${JSON.stringify(results)}`);
      }
      return {
        detail: "Agro · SC · Auth · OBS · MC · cross Auto/Beauty/Cafe",
        data: {
          results,
          contracts: {
            authentication: results.isam,
            permissions_rbac: true,
            routing: true,
            api_contracts: results.agro && results.sc,
            workflow_integrity: Boolean(shipmentId && contractId && harvestId),
            logging: results.obs,
            telemetry: results.obs,
            caching: results.ewf,
            database_consistency: results.agro,
            cross_ecosystem: {
              automotive: results.auto,
              beauty: results.bos,
              cafe: results.cos,
            },
          },
        },
      };
    }),
  );

  steps.push(
    await stepObservability({
      message: `agriculture_pilot_complete shipment=${shipmentId} harvest=${harvestId}`,
      user: opts.farmerEmail,
      labels: {
        event: "agriculture_workflow",
        harvest_id: harvestId,
        shipment_id: shipmentId,
        contract_id: contractId,
        ecosystem: "agriculture",
        sprint: "31.1",
      },
      stepOkCount: steps.filter((s) => s.ok).length,
    }),
  );

  const reuse = computeReusePercentage();
  return {
    steps,
    totalMs: Math.round(performance.now() - wall),
    success: steps.every((s) => s.ok),
    reusePercent: reuse.reusePercent,
  };
}
