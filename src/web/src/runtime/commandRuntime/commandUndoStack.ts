/**
 * Undo / Redo stack · groups · transactions — Sprint 28.7.
 */

import type { CommandArgs, CommandKind, UndoableCommand } from "./commandTypes";

const MAX = 80;
const undoStack: UndoableCommand[] = [];
const redoStack: UndoableCommand[] = [];

let applying = false;
let activeGroupId: string | null = null;
let activeTxnId: string | null = null;
let txnBuffer: UndoableCommand[] = [];

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export const commandUndoStack = {
  isApplying() {
    return applying;
  },

  setApplying(v: boolean) {
    applying = v;
  },

  push(partial: {
    commandId: string;
    action: string;
    label: string;
    args?: CommandArgs;
    previousPath: string;
    route?: string;
    kind: CommandKind;
  }) {
    if (applying) return null;
    const entry: UndoableCommand = {
      id: uid("undo"),
      commandId: partial.commandId,
      action: partial.action,
      label: partial.label,
      args: partial.args || {},
      previousPath: partial.previousPath,
      route: partial.route,
      kind: partial.kind,
      at: new Date().toISOString(),
      groupId: activeGroupId || undefined,
      transactionId: activeTxnId || undefined,
    };
    if (activeTxnId) {
      txnBuffer.push(entry);
      return entry;
    }
    undoStack.unshift(entry);
    if (undoStack.length > MAX) undoStack.length = MAX;
    redoStack.length = 0;
    return entry;
  },

  /** Peek undo stack (newest first). */
  undoEntries(limit = 40): UndoableCommand[] {
    return undoStack.slice(0, limit);
  },

  redoEntries(limit = 40): UndoableCommand[] {
    return redoStack.slice(0, limit);
  },

  /** Alias for inspector / API. */
  history(limit = 40) {
    return {
      undo: this.undoEntries(limit),
      redo: this.redoEntries(limit),
    };
  },

  clearHistory() {
    undoStack.length = 0;
    redoStack.length = 0;
    txnBuffer = [];
    activeGroupId = null;
    activeTxnId = null;
  },

  beginGroup(label = "group") {
    activeGroupId = uid(`grp_${label}`.replace(/\s+/g, "_").slice(0, 24));
    return activeGroupId;
  },

  endGroup() {
    const id = activeGroupId;
    activeGroupId = null;
    return id;
  },

  beginTransaction() {
    activeTxnId = uid("txn");
    txnBuffer = [];
    return activeTxnId;
  },

  commitTransaction() {
    if (!activeTxnId) return null;
    const id = activeTxnId;
    // Collapse transaction into one logical undo unit (newest first in buffer)
    if (txnBuffer.length) {
      const first = txnBuffer[0]!;
      const last = txnBuffer[txnBuffer.length - 1]!;
      undoStack.unshift({
        ...last,
        id: uid("undo"),
        label: `Transaction (${txnBuffer.length})`,
        previousPath: first.previousPath,
        transactionId: id,
        args: { ...last.args, __txnSteps: txnBuffer.map((e) => e.id) },
      });
      if (undoStack.length > MAX) undoStack.length = MAX;
      redoStack.length = 0;
    }
    activeTxnId = null;
    txnBuffer = [];
    return id;
  },

  rollbackTransaction() {
    const buffered = [...txnBuffer];
    activeTxnId = null;
    txnBuffer = [];
    return buffered;
  },

  /** Pop next undo entry (or group of same groupId). */
  popUndo(): UndoableCommand[] {
    const top = undoStack.shift();
    if (!top) return [];
    const batch = [top];
    if (top.groupId) {
      while (undoStack[0]?.groupId === top.groupId) {
        batch.push(undoStack.shift()!);
      }
    }
    for (const e of batch) redoStack.unshift(e);
    if (redoStack.length > MAX) redoStack.length = MAX;
    return batch;
  },

  popRedo(): UndoableCommand[] {
    const top = redoStack.shift();
    if (!top) return [];
    const batch = [top];
    if (top.groupId) {
      while (redoStack[0]?.groupId === top.groupId) {
        batch.push(redoStack.shift()!);
      }
    }
    for (const e of batch) undoStack.unshift(e);
    if (undoStack.length > MAX) undoStack.length = MAX;
    return batch;
  },

  canUndo() {
    return undoStack.length > 0;
  },

  canRedo() {
    return redoStack.length > 0;
  },
};
