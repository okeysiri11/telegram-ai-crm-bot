import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useLayoutStore } from '../../stores/layoutStore';
import { useAuthStore } from '../../stores/authStore';
import { widgetsForRole } from '../../widgets/registry';
import { WidgetShell } from './WidgetShell';
import type { LayoutItem } from '../../types/widgets';

function SortableWidget({ item }: { item: LayoutItem }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id,
  });
  const editMode = useLayoutStore((s) => s.editMode);

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    gridColumn: `span ${item.w}`,
    opacity: isDragging ? 0.6 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} className="min-h-48">
      {editMode && (
        <button
          type="button"
          className="mb-1 w-full cursor-grab rounded bg-slate-200 px-2 py-1 text-xs dark:bg-slate-700"
          {...attributes}
          {...listeners}
        >
          Drag
        </button>
      )}
      <WidgetShell widgetId={item.widgetId} />
    </div>
  );
}

export function WidgetGrid() {
  const items = useLayoutStore((s) => s.items);
  const setItems = useLayoutStore((s) => s.setItems);
  const editMode = useLayoutStore((s) => s.editMode);
  const toggleEditMode = useLayoutStore((s) => s.toggleEditMode);
  const resetLayout = useLayoutStore((s) => s.resetLayout);
  const hasRole = useAuthStore((s) => s.hasRole);

  const allowedIds = new Set(widgetsForRole(hasRole).map((w) => w.id));
  const visibleItems = items.filter((i) => allowedIds.has(i.widgetId));

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const onDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = visibleItems.findIndex((i) => i.id === active.id);
    const newIndex = visibleItems.findIndex((i) => i.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;

    const next = [...visibleItems];
    const [moved] = next.splice(oldIndex, 1);
    next.splice(newIndex, 0, moved);
    setItems(next);
  };

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Operations Dashboard</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={toggleEditMode}
            className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            {editMode ? 'Done' : 'Edit layout'}
          </button>
          <button
            type="button"
            onClick={resetLayout}
            className="rounded-lg border border-[var(--color-border)] px-3 py-1.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            Reset
          </button>
        </div>
      </div>

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
        <SortableContext items={visibleItems.map((i) => i.id)} strategy={rectSortingStrategy}>
          <div className="grid grid-cols-12 gap-4">
            {visibleItems.map((item) => (
              <SortableWidget key={item.id} item={item} />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
}
