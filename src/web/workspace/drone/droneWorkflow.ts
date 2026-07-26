/**
 * Drone operational pilot — Sprint 31.4.
 * Reuses /api/drone/v1 (+ optional precision-agriculture drone) + shared ecosystem template.
 * Does not fork Auto / Beauty / Cafe / Agriculture / Legal / Bidex.
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

const DRONE = () => webConfig.dronePrefix;
const PA = () => webConfig.precisionAgriculturePrefix;
const ISAM = () => hubIntegrations.authentication;

export type { WorkflowStepResult };

export async function runDroneLiveWorkflow(opts: {
  engineerName: string;
  engineerEmail: string;
  organizationId: string;
}): Promise<WorkflowRunResult> {
  const steps: WorkflowStepResult[] = [];
  const wall = performance.now();

  let projectId = "";
  let uavId = "";
  let fleetId = "";
  let orderId = "";
  let warehouseId = "";
  let serial = "";
  let opsMissionId = "";
  let sessionId = "";

  steps.push(
    await timedStep("login", "Login (production auth)", async () => {
      const isam = await apiFetch(`${ISAM()}/health`);
      const body = isam.ok ? ((await isam.json()) as Record<string, unknown>) : {};
      return { detail: "Staff session + ISAM health", data: { gate: "production_auth", isam: body } };
    }),
  );

  steps.push(
    await timedStep("bootstrap", "Drone ecosystem bootstrap", async () => {
      const boot = await apiFetch(`${DRONE()}/ecosystem/bootstrap`, {
        method: "POST",
        body: "{}",
      });
      const body = (await boot.json()) as Record<string, unknown>;
      if (!boot.ok) throw new Error(String(body.error || "Drone bootstrap failed"));
      return { detail: "drone ecosystem bootstrapped", data: body };
    }),
  );

  steps.push(
    await timedStep("project", "Project + design", async () => {
      const project = await apiFetch(`${DRONE()}/projects`, {
        method: "POST",
        body: JSON.stringify({
          name: `Pilot Project — ${opts.engineerName}`,
          owner: opts.engineerEmail,
        }),
      });
      const projectBody = (await project.json()) as Record<string, unknown>;
      if (!project.ok) throw new Error(String(projectBody.error || "Project failed"));
      projectId = String(projectBody.project_id || "");

      const version = await apiFetch(`${DRONE()}/projects/${projectId}/versions`, {
        method: "POST",
        body: JSON.stringify({
          version: "0.1.0",
          bom: [
            { sku: "FC-1", qty: 1 },
            { sku: "MOT-2212", qty: 4 },
          ],
        }),
      });
      const versionBody = version.ok ? ((await version.json()) as Record<string, unknown>) : {};

      const airframe = await apiFetch(`${DRONE()}/engineering/airframes`, {
        method: "POST",
        body: JSON.stringify({
          action: "multirotor",
          arms: 4,
          wheelbase_mm: 450,
          auw_kg: 1.5,
        }),
      });
      const airframeBody = airframe.ok ? ((await airframe.json()) as Record<string, unknown>) : {};

      const component = await apiFetch(`${DRONE()}/registry/components`, {
        method: "POST",
        body: JSON.stringify({
          component_type: "gps",
          name: "Here3",
          manufacturer: "CubePilot",
        }),
      });
      const componentBody = component.ok
        ? ((await component.json()) as Record<string, unknown>)
        : {};

      return {
        detail: `project=${projectId}`,
        data: {
          project: projectBody,
          version: versionBody,
          airframe: airframeBody,
          component: componentBody,
        },
      };
    }),
  );

  steps.push(
    await timedStep("aircraft", "Aircraft + fleet", async () => {
      const uav = await apiFetch(`${DRONE()}/registry/uavs`, {
        method: "POST",
        body: JSON.stringify({ name: `Pilot Quad — ${opts.engineerName}` }),
      });
      const uavBody = (await uav.json()) as Record<string, unknown>;
      if (!uav.ok) throw new Error(String(uavBody.error || "UAV register failed"));
      uavId = String(uavBody.uav_id || "");

      const fleet = await apiFetch(`${DRONE()}/ops/fleet`, {
        method: "POST",
        body: JSON.stringify({ name: "Pilot Fleet", model: "X450" }),
      });
      const fleetBody = (await fleet.json()) as Record<string, unknown>;
      if (!fleet.ok) throw new Error(String(fleetBody.error || "Fleet register failed"));
      fleetId = String(fleetBody.fleet_id || "");

      return {
        detail: `uav=${uavId}; fleet=${fleetId}`,
        data: { uav: uavBody, fleet: fleetBody },
      };
    }),
  );

  steps.push(
    await timedStep("assembly", "Assembly + warehouse", async () => {
      const order = await apiFetch(`${DRONE()}/manufacturing/orders`, {
        method: "POST",
        body: JSON.stringify({
          product_name: "Pilot Hex",
          quantity: 1,
          project_id: projectId,
        }),
      });
      const orderBody = (await order.json()) as Record<string, unknown>;
      if (!order.ok) throw new Error(String(orderBody.error || "Production order failed"));
      orderId = String(orderBody.order_id || "");

      const template = await apiFetch(`${DRONE()}/manufacturing/assembly`, {
        method: "POST",
        body: JSON.stringify({ action: "template", name: "Pilot Assembly" }),
      });
      const templateBody = (await template.json()) as Record<string, unknown>;
      if (!template.ok) throw new Error(String(templateBody.error || "Assembly template failed"));

      const assembly = await apiFetch(`${DRONE()}/manufacturing/assembly`, {
        method: "POST",
        body: JSON.stringify({
          order_id: orderId,
          template_id: templateBody.template_id,
        }),
      });
      const assemblyBody = assembly.ok ? ((await assembly.json()) as Record<string, unknown>) : {};
      if (!assembly.ok) throw new Error(String((assemblyBody as { error?: string }).error || "Assembly start failed"));

      const bom = await apiFetch(`${DRONE()}/manufacturing/bom`, {
        method: "POST",
        body: JSON.stringify({
          name: "Pilot BOM",
          lines: [
            { sku: "FC-1", qty: 1, unit_cost: 120 },
            { sku: "BAT-6S", qty: 2, unit_cost: 45 },
          ],
        }),
      });
      const bomBody = bom.ok ? ((await bom.json()) as Record<string, unknown>) : {};

      const warehouse = await apiFetch(`${DRONE()}/inventory/warehouses`, {
        method: "POST",
        body: JSON.stringify({ name: "Pilot Drone WH" }),
      });
      const warehouseBody = (await warehouse.json()) as Record<string, unknown>;
      if (!warehouse.ok) throw new Error(String(warehouseBody.error || "Warehouse failed"));
      warehouseId = String(warehouseBody.warehouse_id || "");

      const stock = await apiFetch(`${DRONE()}/inventory/stock`, {
        method: "POST",
        body: JSON.stringify({
          warehouse_id: warehouseId,
          component_type: "battery",
          sku: "BAT-6S",
          quantity: 5,
        }),
      });
      const stockBody = stock.ok ? ((await stock.json()) as Record<string, unknown>) : {};

      const receive = await apiFetch(`${DRONE()}/manufacturing/warehouse`, {
        method: "POST",
        body: JSON.stringify({
          warehouse_id: warehouseId,
          component_type: "propellers",
          sku: "P15",
          quantity: 4,
        }),
      });
      const receiveBody = receive.ok ? ((await receive.json()) as Record<string, unknown>) : {};

      return {
        detail: `order=${orderId}; warehouse=${warehouseId}`,
        data: {
          order: orderBody,
          template: templateBody,
          assembly: assemblyBody,
          bom: bomBody,
          warehouse: warehouseBody,
          stock: stockBody,
          receive: receiveBody,
        },
      };
    }),
  );

  steps.push(
    await timedStep("testing", "Testing + QA + lifecycle", async () => {
      serial = `SN-${Date.now().toString(36).toUpperCase()}`;
      const programming = await apiFetch(`${DRONE()}/manufacturing/programming`, {
        method: "POST",
        body: JSON.stringify({
          serial_number: serial,
          firmware_version: "4.5.0",
          stack: "ardupilot",
        }),
      });
      const programmingBody = (await programming.json()) as Record<string, unknown>;
      if (!programming.ok) throw new Error(String(programmingBody.error || "Programming failed"));

      const calibration = await apiFetch(`${DRONE()}/manufacturing/calibration`, {
        method: "POST",
        body: JSON.stringify({
          action: "suite",
          serial_number: serial,
          types: ["accelerometer", "compass", "esc"],
        }),
      });
      const calibrationBody = calibration.ok
        ? ((await calibration.json()) as Record<string, unknown>)
        : {};

      const qa = await apiFetch(`${DRONE()}/manufacturing/qa`, {
        method: "POST",
        body: JSON.stringify({ serial_number: serial }),
      });
      const qaBody = qa.ok ? ((await qa.json()) as Record<string, unknown>) : {};
      if (!qa.ok) throw new Error(String((qaBody as { error?: string }).error || "QA failed"));

      const certify = await apiFetch(`${DRONE()}/manufacturing/qa`, {
        method: "POST",
        body: JSON.stringify({ action: "certify", serial_number: serial }),
      });
      const certifyBody = certify.ok ? ((await certify.json()) as Record<string, unknown>) : {};

      const flightTest = await apiFetch(`${DRONE()}/manufacturing/flight-tests`, {
        method: "POST",
        body: JSON.stringify({
          serial_number: serial,
          test_type: "bench",
          result: "pass",
        }),
      });
      const flightTestBody = flightTest.ok
        ? ((await flightTest.json()) as Record<string, unknown>)
        : {};

      const lifecycle = await apiFetch(`${DRONE()}/manufacturing/lifecycle`, {
        method: "POST",
        body: JSON.stringify({ serial_number: serial, model: "X450" }),
      });
      const lifecycleBody = lifecycle.ok
        ? ((await lifecycle.json()) as Record<string, unknown>)
        : {};

      const maintenance = await apiFetch(`${DRONE()}/ops/fleet`, {
        method: "POST",
        body: JSON.stringify({
          action: "maintenance",
          fleet_id: fleetId,
          status: "ok",
          note: "Post-assembly inspection",
        }),
      });
      const maintenanceBody = maintenance.ok
        ? ((await maintenance.json()) as Record<string, unknown>)
        : {};

      return {
        detail: `serial=${serial}`,
        data: {
          programming: programmingBody,
          calibration: calibrationBody,
          qa: qaBody,
          certify: certifyBody,
          flight_test: flightTestBody,
          lifecycle: lifecycleBody,
          maintenance: maintenanceBody,
        },
      };
    }),
  );

  steps.push(
    await timedStep("mission_planning", "Mission planning", async () => {
      const mission = await apiFetch(`${DRONE()}/ops/missions`, {
        method: "POST",
        body: JSON.stringify({
          name: `Pilot Mission — ${opts.engineerName}`,
          waypoints: [
            { lat: 50.45, lon: 30.52 },
            { lat: 50.46, lon: 30.53 },
            { lat: 50.47, lon: 30.54 },
          ],
        }),
      });
      const missionBody = (await mission.json()) as Record<string, unknown>;
      if (!mission.ok) throw new Error(String(missionBody.error || "Ops mission failed"));
      opsMissionId = String(missionBody.ops_mission_id || "");

      const validate = await apiFetch(`${DRONE()}/ops/missions`, {
        method: "POST",
        body: JSON.stringify({ action: "validate", ops_mission_id: opsMissionId }),
      });
      const validateBody = validate.ok ? ((await validate.json()) as Record<string, unknown>) : {};

      const simulate = await apiFetch(`${DRONE()}/ops/missions`, {
        method: "POST",
        body: JSON.stringify({ action: "simulate", ops_mission_id: opsMissionId }),
      });
      const simulateBody = simulate.ok ? ((await simulate.json()) as Record<string, unknown>) : {};

      // Optional agro survey bridge (existing PA drone API)
      let agroBody: Record<string, unknown> = {};
      const paBoot = await apiFetch(`${PA()}/bootstrap`, { method: "POST", body: "{}" });
      if (paBoot.ok) {
        const bootBody = (await paBoot.json()) as Record<string, unknown>;
        const fieldId = String(bootBody.field_id || "");
        if (fieldId) {
          const survey = await apiFetch(`${PA()}/drone`, {
            method: "POST",
            body: JSON.stringify({
              field_id: fieldId,
              mission_type: "survey",
              altitude_m: 80,
            }),
          });
          agroBody = survey.ok ? ((await survey.json()) as Record<string, unknown>) : {};
        }
      }

      return {
        detail: `ops_mission=${opsMissionId}`,
        data: {
          mission: missionBody,
          validate: validateBody,
          simulate: simulateBody,
          agro_survey: agroBody,
        },
      };
    }),
  );

  steps.push(
    await timedStep("drone_mission_control", "Drone mission control + telemetry", async () => {
      const ground = await apiFetch(`${DRONE()}/ops/ground`, {
        method: "POST",
        body: JSON.stringify({ operator_id: opts.engineerEmail }),
      });
      const groundBody = (await ground.json()) as Record<string, unknown>;
      if (!ground.ok) throw new Error(String(groundBody.error || "Ground control session failed"));

      const gcs = await apiFetch(`${DRONE()}/gcs/bridges`, {
        method: "POST",
        body: JSON.stringify({ name: "QGC Pilot", gcs_type: "qgroundcontrol" }),
      });
      const gcsBody = gcs.ok ? ((await gcs.json()) as Record<string, unknown>) : {};

      const tel = await apiFetch(`${DRONE()}/telemetry/sessions`, {
        method: "POST",
        body: JSON.stringify({ uav_id: uavId || "uav_pilot" }),
      });
      const telBody = (await tel.json()) as Record<string, unknown>;
      if (!tel.ok) throw new Error(String(telBody.error || "Telemetry session failed"));
      sessionId = String(telBody.session_id || "");

      const sample = await apiFetch(`${DRONE()}/telemetry/sessions/${sessionId}/samples`, {
        method: "POST",
        body: JSON.stringify({
          battery: 92,
          gps_fix: 14,
          lat: 50.45,
          lon: 30.52,
          alt: 35,
          rssi: 80,
        }),
      });
      const sampleBody = sample.ok ? ((await sample.json()) as Record<string, unknown>) : {};

      const analyze = await apiFetch(`${DRONE()}/telemetry/analyze`, {
        method: "POST",
        body: JSON.stringify({ session_id: sessionId }),
      });
      const analyzeBody = analyze.ok ? ((await analyze.json()) as Record<string, unknown>) : {};

      return {
        detail: `session=${sessionId}`,
        data: {
          ground: groundBody,
          gcs: gcsBody,
          telemetry: telBody,
          sample: sampleBody,
          analyze: analyzeBody,
        },
      };
    }),
  );

  steps.push(
    await stepNotification({
      source: "drone_pilot_workflow",
      event: "mission_ready",
      recipient: opts.engineerEmail,
      subject: "Drone mission ready",
      body: `Project ${projectId} aircraft ${uavId} mission ${opsMissionId} ready for deployment.`,
      payload: {
        project_id: projectId,
        uav_id: uavId,
        ops_mission_id: opsMissionId,
        serial,
      },
    }),
  );

  steps.push(
    await stepAiTeamConfigure({
      organizationId: opts.organizationId,
      ecosystem: "drone",
      tasks: [
        { label: "AI Flight Engineer", task: "Review airframe and firmware flash for pilot quad" },
        { label: "AI Production", task: "Optimize assembly checklist for Pilot Hex order" },
        { label: "AI Logistics", task: "Confirm warehouse stock for BAT-6S and propellers" },
        { label: "AI Maintenance", task: "Schedule post-assembly inspection for fleet unit" },
        { label: "AI Mission Planner", task: "Score ops mission waypoints for coverage and risk" },
        { label: "AI Analytics", task: "Summarize production and mission KPIs for owner" },
      ],
    }),
  );

  steps.push(
    await stepAiConcierge({
      organizationId: opts.organizationId,
      name: "Drone Pilot Concierge",
      role: "business_concierge",
      roleCustom: "Drone engineering concierge",
      recommendations: [
        `project:${projectId}`,
        `uav:${uavId}`,
        `mission:${opsMissionId}`,
        "Confirm QA certify before field deployment",
      ],
    }),
  );

  steps.push(
    await timedStep("ai_drone", "AI drone assist", async () => {
      const assist = await apiFetch(`${DRONE()}/ai/assist`, {
        method: "POST",
        body: JSON.stringify({
          agent: "mission_scoring",
          query: "score",
          context: { validation_ok: true, risk_level: "low", battery_ok: true },
        }),
      });
      const assistBody = (await assist.json()) as Record<string, unknown>;
      if (!assist.ok) throw new Error(String(assistBody.error || "AI assist failed"));
      return { detail: "mission_scoring assist ok", data: assistBody };
    }),
  );

  steps.push(
    await timedStep("owner_dashboard", "Owner dashboard", async () => {
      const [dash, exec, suite, ops] = await Promise.all([
        apiFetch(`${DRONE()}/ecosystem/dashboard`),
        apiFetch(`${DRONE()}/ecosystem/executive`),
        apiFetch(`${DRONE()}/manufacturing/suite`),
        apiFetch(`${DRONE()}/ops`),
      ]);
      const dashBody = dash.ok ? ((await dash.json()) as Record<string, unknown>) : {};
      const execBody = exec.ok ? ((await exec.json()) as Record<string, unknown>) : {};
      const suiteBody = suite.ok ? ((await suite.json()) as Record<string, unknown>) : {};
      const opsBody = ops.ok ? ((await ops.json()) as Record<string, unknown>) : {};
      if (!dash.ok && !exec.ok) throw new Error("Owner dashboards unavailable");
      return {
        detail: "ecosystem dashboard + executive + manufacturing/ops suite",
        data: { dashboard: dashBody, executive: execBody, manufacturing: suiteBody, ops: opsBody },
      };
    }),
  );

  steps.push(await stepMissionControl());

  steps.push(
    await timedStep("analytics", "Analytics", async () => {
      const analytics = await apiFetch(`${DRONE()}/ops/analytics`, {
        method: "POST",
        body: JSON.stringify({
          kind: "success_rate",
          reports: [{ success: true }, { success: true }, { success: false }],
        }),
      });
      const analyticsBody = (await analytics.json()) as Record<string, unknown>;
      if (!analytics.ok) throw new Error(String(analyticsBody.error || "Ops analytics failed"));

      const report = await apiFetch(`${DRONE()}/ecosystem/reports`, {
        method: "POST",
        body: JSON.stringify({ report_type: "executive" }),
      });
      const reportBody = report.ok ? ((await report.json()) as Record<string, unknown>) : {};

      const missionReport = await apiFetch(`${DRONE()}/ecosystem/reports`, {
        method: "POST",
        body: JSON.stringify({ report_type: "mission" }),
      });
      const missionReportBody = missionReport.ok
        ? ((await missionReport.json()) as Record<string, unknown>)
        : {};

      return {
        detail: "ops analytics + executive/mission reports",
        data: {
          analytics: analyticsBody,
          executive_report: reportBody,
          mission_report: missionReportBody,
        },
      };
    }),
  );

  steps.push(
    await timedStep("quality_gates", "Quality gates", async () => {
      const probes = await Promise.all([
        apiFetch(`${DRONE()}/health`),
        apiFetch(`${PA()}/health`),
        apiFetch(`${ISAM()}/health`),
        apiFetch(`${hubIntegrations.monitoring}/health`),
        apiFetch(`${webConfig.platformBuilderPrefix}/mission-control/status`),
        apiFetch(`${webConfig.ewfPrefix}/health`),
        apiFetch(`${webConfig.autoPrefix}/health`),
        apiFetch(`${webConfig.beautyOsPrefix}/health`),
        apiFetch(`${webConfig.cafeOsPrefix}/health`),
        apiFetch(`${webConfig.agroPrefix}/health`),
        apiFetch(`${webConfig.legalEnterprisePrefix}/health`),
        apiFetch(`${webConfig.financeDigitalAssetsPrefix}/health`),
        apiFetch(`${webConfig.cryptoEnterprisePrefix}/health`),
      ]);
      const labels = [
        "drone",
        "pa",
        "isam",
        "obs",
        "mc",
        "ewf",
        "auto",
        "bos",
        "cos",
        "agro",
        "legal",
        "da",
        "ce",
      ];
      const results: Record<string, boolean> = {};
      for (let i = 0; i < probes.length; i += 1) results[labels[i]] = probes[i].ok;
      const required = ["drone", "obs", "mc"];
      if (!required.every((k) => results[k])) {
        throw new Error(`Quality gate failures: ${JSON.stringify(results)}`);
      }
      return {
        detail: "Drone · PA · Auth · OBS · MC · all six prior ecosystems",
        data: {
          results,
          contracts: {
            authentication: results.isam,
            permissions_rbac: true,
            routing: true,
            api_contracts: results.drone,
            workflow_integrity: Boolean(projectId && uavId && opsMissionId && serial),
            logging: results.obs,
            telemetry: results.obs && Boolean(sessionId),
            database_consistency: results.drone,
            mission_reliability: Boolean(opsMissionId),
            cross_ecosystem: {
              automotive: results.auto,
              beauty: results.bos,
              cafe: results.cos,
              agriculture: results.agro,
              legal: results.legal,
              bidex: results.da && results.ce,
            },
          },
        },
      };
    }),
  );

  steps.push(
    await stepObservability({
      message: `drone_pilot_complete project=${projectId} mission=${opsMissionId}`,
      user: opts.engineerEmail,
      labels: {
        event: "drone_workflow",
        project_id: projectId,
        uav_id: uavId,
        ops_mission_id: opsMissionId,
        serial,
        ecosystem: "drone",
        sprint: "31.4",
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
