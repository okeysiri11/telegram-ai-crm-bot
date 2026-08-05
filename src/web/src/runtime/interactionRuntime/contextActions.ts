/**
 * Context action executor — real Runtime operations only — Sprint 29.6.
 */

import { enterpriseEventBus } from "@/integration-hub/enterpriseEventBus";
import { businessNetworkEngine, EBN_HOME_PROFILE_ID, EBN_PARTNER_PROFILE_ID } from "@/runtime/businessNetwork";
import { digitalCitizenEngine, EDC_CITIZEN_OWNER } from "@/runtime/digitalCitizen";
import { lifeEngine } from "@/runtime/lifeEngine";
import { assetRuntime } from "@/runtime/assetRuntime";
import { workflowRuntime } from "@/runtime/workflowRuntime";
import { cityVisualizationRuntime } from "@/runtime/cityVisualization";
import type { ActionResult, InteractionActionId, InteractionTarget } from "./interactionTypes";
import { interactionRegistry } from "./interactionRegistry";
import { interactionPermissions } from "./interactionPermissions";
import { navigationEngine } from "./navigationEngine";
import { publishInteractionEvent } from "./interactionEvents";
import { interactionHistory, interactionSessionStore } from "./interactionSession";

function openRoute(path: string, extra?: Record<string, unknown>) {
  enterpriseEventBus.openModule(path, "hub", extra);
  enterpriseEventBus.navigate(path, "hub");
}

export function executeContextAction(
  actionId: InteractionActionId,
  target?: InteractionTarget,
  args: Record<string, unknown> = {},
): ActionResult {
  const def = interactionRegistry.getAction(actionId);
  if (!def) {
    return { ok: false, actionId, error: "action_not_found" };
  }

  const session = interactionSessionStore.active();
  const scopes = interactionPermissions.scopesForActor({
    citizenId: session?.context.actorCitizenId || String(args.actorCitizenId || EDC_CITIZEN_OWNER),
    companyId: session?.context.actorCompanyId || String(args.actorCompanyId || EBN_HOME_PROFILE_ID),
    isAdmin: Boolean(args.isAdmin),
    isManager: Boolean(args.isManager) || true,
  });

  if (!interactionPermissions.canExecuteAction(actionId, scopes)) {
    interactionHistory.recordEvent("action", {
      actionId,
      target,
      result: "denied",
      message: "permission_denied",
    });
    return { ok: false, actionId, error: "permission_denied" };
  }

  let result: ActionResult = { ok: false, actionId, error: "not_implemented" };

  switch (actionId) {
    case "open_building": {
      const id = target?.id || String(args.buildingId || "hub");
      const t = target || navigationEngine.find("building", id);
      const path = t?.route || "/enterprise-city";
      openRoute(path, { buildingId: id });
      navigationEngine.pushNavigation(path, t || undefined, t?.label);
      cityVisualizationRuntime.rebuildScene("BuildingUpdated");
      result = { ok: true, actionId, route: path, message: id, data: { buildingId: id } };
      publishInteractionEvent("ObjectOpened", { kind: "building", id });
      break;
    }
    case "open_company": {
      const id = target?.kind === "company" ? target.id : String(args.companyId || target?.companyId || EBN_HOME_PROFILE_ID);
      const profile = businessNetworkEngine.getProfile(id);
      const path = "/business-network";
      openRoute(path, { profileId: id });
      navigationEngine.pushNavigation(path, target || navigationEngine.find("company", id) || undefined);
      result = {
        ok: !!profile,
        actionId,
        route: path,
        message: profile?.companyName || id,
        error: profile ? undefined : "company_not_found",
        data: { companyId: id },
      };
      if (profile) publishInteractionEvent("ObjectOpened", { kind: "company", id });
      break;
    }
    case "open_citizen": {
      const id = target?.id || String(args.citizenId || EDC_CITIZEN_OWNER);
      const citizen = digitalCitizenEngine.getCitizen(id);
      const path = "/digital-citizens";
      openRoute(path, { citizenId: id });
      navigationEngine.pushNavigation(path, target || navigationEngine.find("citizen", id) || undefined);
      result = {
        ok: !!citizen,
        actionId,
        route: path,
        message: citizen?.displayName || id,
        error: citizen ? undefined : "citizen_not_found",
      };
      if (citizen) publishInteractionEvent("ObjectOpened", { kind: "citizen", id });
      break;
    }
    case "open_asset":
    case "open_vehicle": {
      const id = target?.id || String(args.assetId || "");
      const asset = assetRuntime.get(id);
      const path = "/assets";
      openRoute(path, { assetId: id });
      navigationEngine.pushNavigation(path, target || undefined);
      result = {
        ok: !!asset,
        actionId,
        route: path,
        message: asset?.profile.name || id,
        error: asset ? undefined : "asset_not_found",
      };
      if (asset) publishInteractionEvent("ObjectOpened", { kind: target?.kind || "asset", id });
      break;
    }
    case "open_district": {
      const id = target?.id || String(args.districtId || "enterprise");
      const path = "/spatial";
      openRoute(path, { districtId: id });
      navigationEngine.pushNavigation(path, target || navigationEngine.find("district", id) || undefined);
      result = { ok: true, actionId, route: path, message: id };
      publishInteractionEvent("ObjectOpened", { kind: "district", id });
      break;
    }
    case "open_project": {
      const id = target?.id || String(args.projectId || "");
      const path = "/life-engine";
      openRoute(path, { projectId: id });
      navigationEngine.pushNavigation(path, target || undefined);
      result = { ok: true, actionId, route: path, message: id };
      publishInteractionEvent("ObjectOpened", { kind: "project", id });
      break;
    }
    case "open_meeting": {
      const id = target?.id || String(args.meetingId || "");
      const meeting = lifeEngine.meetings.get(id);
      const path = "/life-engine";
      openRoute(path, { meetingId: id });
      result = {
        ok: !!meeting,
        actionId,
        route: path,
        message: meeting?.title || id,
        error: meeting ? undefined : "meeting_not_found",
      };
      if (meeting) publishInteractionEvent("ObjectOpened", { kind: "meeting", id });
      break;
    }
    case "navigate": {
      const path =
        String(args.path || "") ||
        target?.route ||
        (target ? interactionRegistry.defaultRoute(target.kind) : "/city-visualization");
      openRoute(path, { targetId: target?.id, targetKind: target?.kind });
      navigationEngine.pushNavigation(path, target, target?.label);
      publishInteractionEvent("NavigationChanged", { path, targetId: target?.id });
      result = { ok: true, actionId, route: path, message: path };
      break;
    }
    case "assign_task": {
      const citizenId = target?.kind === "citizen" ? target.id : String(args.citizenId || EDC_CITIZEN_OWNER);
      const title = String(args.title || `Task for ${citizenId}`);
      const projectId = target?.kind === "project" ? target.id : args.projectId ? String(args.projectId) : undefined;
      const task = digitalCitizenEngine.assignTask(citizenId, title, args.dueAt ? String(args.dueAt) : undefined, projectId);
      result = {
        ok: !!task,
        actionId,
        message: title,
        data: { citizenId, projectId, task },
        error: task ? undefined : "assign_failed",
      };
      break;
    }
    case "create_meeting": {
      const hostCitizenId = String(args.hostCitizenId || session?.context.actorCitizenId || EDC_CITIZEN_OWNER);
      const buildingId =
        target?.buildingId ||
        (target?.kind === "building" ? target.id : undefined) ||
        String(args.buildingId || "hub");
      const title = String(args.title || `Meeting @ ${buildingId}`);
      const meeting = lifeEngine.createMeeting({
        title,
        hostCitizenId,
        buildingId,
        attendeeIds: Array.isArray(args.attendeeIds) ? (args.attendeeIds as string[]) : undefined,
        companyId: target?.companyId || String(args.companyId || EBN_HOME_PROFILE_ID),
        projectId: args.projectId ? String(args.projectId) : undefined,
      });
      result = {
        ok: !!meeting,
        actionId,
        message: meeting.title,
        data: { meetingId: meeting.id, buildingId },
      };
      break;
    }
    case "invite_partner": {
      const toProfileId =
        target?.kind === "company" && target.id !== EBN_HOME_PROFILE_ID
          ? target.id
          : String(args.toProfileId || EBN_PARTNER_PROFILE_ID);
      const fromProfileId = String(args.fromProfileId || EBN_HOME_PROFILE_ID);
      const res = businessNetworkEngine.createRelationship({
        fromProfileId,
        toProfileId,
        type: "partner",
        notes: String(args.notes || "Interaction Runtime invite"),
        actorId: fromProfileId,
      });
      result = {
        ok: res.ok,
        actionId,
        message: toProfileId,
        data: { relationshipId: res.relationship?.id },
        error: res.ok ? undefined : res.error || "invite_failed",
      };
      break;
    }
    case "launch_ai": {
      const aiId = target?.kind === "ai_agent" ? target.id : String(args.aiId || "");
      const agents = digitalCitizenEngine.listAi();
      const agent = aiId ? agents.find((a) => a.id === aiId) : agents[0];
      const path = "/digital-citizens";
      openRoute(path, { aiId: agent?.id });
      result = {
        ok: !!agent,
        actionId,
        route: path,
        message: agent?.name || "ai",
        data: { aiId: agent?.id, kind: agent?.kind },
        error: agent ? undefined : "ai_not_found",
      };
      if (agent) publishInteractionEvent("ObjectOpened", { kind: "ai_agent", id: agent.id });
      break;
    }
    case "start_workflow": {
      const defs = workflowRuntime.listDefinitions();
      const definitionId = String(args.definitionId || defs[0]?.id || "");
      if (!definitionId) {
        result = { ok: false, actionId, error: "workflow_not_found" };
        break;
      }
      // fire-and-forget start; callers may await via workflowRuntime directly
      void workflowRuntime
        .start(definitionId, {
          ...(args.vars as Record<string, unknown> | undefined),
          interactionTargetId: target?.id,
          interactionTargetKind: target?.kind,
        })
        .then((res) => {
          if (res.ok) {
            publishInteractionEvent("WorkflowStarted", {
              definitionId,
              sessionId: res.sessionId,
              targetId: target?.id,
            });
          }
        });
      publishInteractionEvent("WorkflowStarted", { definitionId, targetId: target?.id, pending: true });
      result = {
        ok: true,
        actionId,
        message: definitionId,
        data: { definitionId },
        route: "/workflow-runtime",
      };
      openRoute("/workflow-runtime", { definitionId });
      break;
    }
    default:
      result = { ok: false, actionId, error: "unknown_action" };
  }

  publishInteractionEvent("ActionExecuted", {
    actionId,
    ok: result.ok,
    targetId: target?.id,
    targetKind: target?.kind,
    error: result.error,
  });
  interactionHistory.recordEvent("action", {
    actionId,
    target,
    result: result.ok ? "ok" : result.error === "permission_denied" ? "denied" : "error",
    message: result.message || result.error,
    payload: result.data,
  });

  return result;
}

export function contextActionsForTarget(target: InteractionTarget) {
  return interactionRegistry.actionsForKind(target.kind);
}
