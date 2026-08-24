/** AUTO 1.0 — Russian labels for the private import OS. */

export const STATUS_RU: Record<string, string> = {
  INTEREST: "Интерес",
  AUCTION: "Аукцион",
  WON: "Выигран",
  PURCHASED: "Куплен",
  AWAITING_PICKUP: "Ожидает забора",
  INLAND_TRANSPORT: "Наземная перевозка",
  AT_ORIGIN_PORT: "Порт отправления",
  IN_CONTAINER: "В контейнере",
  SEA_TRANSIT: "Морская перевозка",
  DESTINATION_PORT: "Порт назначения",
  CUSTOMS: "Растаможка",
  CUSTOMS_CLEARED: "Растаможен",
  IN_UKRAINE: "В Украине",
  PREPARATION: "Подготовка",
  READY_FOR_SALE: "Готов к продаже",
  RESERVED: "Зарезервирован",
  SOLD: "Продан",
  CANCELLED: "Отменён",
};

export const EXPENSE_RU: Record<string, string> = {
  PURCHASE: "Цена автомобиля",
  AUCTION_FEE: "Комиссия аукциона",
  INLAND_TRANSPORT: "Доставка по стране покупки",
  SEA_FREIGHT: "Морской фрахт",
  PORT_FEE: "Портовые расходы",
  BROKER: "Брокер",
  CUSTOMS: "Таможенные платежи",
  DUTY: "Мито",
  EXCISE: "Акциз",
  IMPORT_VAT: "НДС на импорт",
  CUSTOMS_PENALTY: "Штраф таможни",
  CERTIFICATION: "Сертификация",
  CERT_LAB: "Орган сертификации",
  REGISTRATION: "Регистрация",
  MREO: "МРЕО",
  TRANSPORT_UA: "Доставка по Украине",
  UA_TRANSPORT: "Автовоз по Украине",
  EU_TRANSPORT: "Автовоз по Европе",
  CONTAINER: "Контейнер",
  FORWARDER: "Экспедитор",
  DEMURRAGE: "Демередж",
  DETENTION: "Детейшн",
  TOW_TRUCK: "Эвакуатор",
  REPAIR: "Ремонт",
  PARTS: "Запчасти",
  STORAGE: "Хранение",
  BANK_FEE: "Банковская комиссия",
  OTHER: "Прочие расходы",
};

export const PHOTO_RU: Record<string, string> = {
  AUCTION: "Аукцион",
  DAMAGE: "Повреждения",
  PICKUP: "Забор",
  PORT: "Порт",
  LOADED: "Загрузка",
  WAREHOUSE: "Склад",
  CONTAINER_LOADING: "Погрузка в контейнер",
  SEAL: "Пломба",
  UNLOADING: "Разгрузка",
  DESTINATION_PORT: "Порт назначения",
  DELIVERY: "Доставка",
  ARRIVAL: "Прибытие",
  CUSTOMS: "Таможня",
  REPAIR: "Ремонт",
  READY_FOR_SALE: "Готов к продаже",
  OTHER: "Другое",
};

export const DOC_RU: Record<string, string> = {
  auction_invoice: "Инвойс аукциона",
  purchase_agreement: "Договор покупки",
  title: "Title / техпаспорт",
  bill_of_sale: "Bill of Sale",
  shipping: "Отгрузочный документ",
  bill_of_lading: "Коносамент (B/L)",
  booking_confirmation: "Подтверждение букинга",
  container_release: "Релиз контейнера",
  gate_pass: "Gate Pass",
  invoice: "Счёт",
  carrier_invoice: "Счёт перевозчика",
  port_invoice: "Портовый счёт",
  packing_list: "Упаковочный лист",
  title_copy: "Копия Title",
  export_document: "Экспортный документ",
  customs_export: "Экспортная таможенная декларация",
  delivery_order: "Delivery Order",
  cmr: "CMR",
  act: "Акт",
  container: "Документ контейнера",
  customs_declaration: "Таможенная декларация",
  broker: "Документы брокера",
  certificate: "Сертификат",
  registration: "Регистрационные документы",
  repair_invoice: "Счёт ремонта",
  sale_agreement: "Договор продажи",
  payment_confirmation: "Подтверждение оплаты",
  transfer_act: "Акт приёма-передачи",
  commercial_offer: "Коммерческое предложение",
  bank_receipt: "Банковская квитанция",
  cash_receipt: "Кассовый чек",
  statement: "Выписка",
  insurance: "Страховка",
  inspection: "Осмотр",
  duty_doc: "Документ пошлины",
  vat_doc: "Документ НДС",
  excise_doc: "Документ акциза",
  tax_id_copy: "Копия ИНН",
  passport: "Паспорт",
  id_card: "ID / удостоверение",
  contract: "Договор",
  other: "Другое",
};

export const ROLE_RU: Record<string, string> = {
  auto_director: "Директор",
  auto_accountant: "Бухгалтер",
  auto_manager: "Менеджер",
  auto_forwarder: "Экспедитор",
  auto_customs: "Ответственный за таможню",
  auto_admin: "Администратор",
  platform_owner: "Владелец платформы",
};

export const CARD_RU: Record<string, string> = {
  vehicles_total: "Автомобилей всего",
  purchased: "Куплено",
  in_transit: "В пути",
  at_port: "В порту",
  at_customs: "На таможне",
  in_ukraine: "В Украине",
  in_preparation: "На подготовке",
  for_sale: "В продаже",
  sold: "Продано",
};

export const FIN_RU: Record<string, string> = {
  purchase_cost: "Стоимость закупки",
  logistics: "Логистика",
  customs: "Таможенные расходы",
  other: "Прочие расходы",
  invested: "Всего вложено",
  expected_revenue: "Ожидаемая выручка",
  actual_revenue: "Фактическая выручка",
  expected_profit: "Ожидаемая прибыль",
  actual_profit: "Фактическая прибыль",
};

export const PURCHASE_STATUSES = ["INTEREST", "AUCTION", "WON", "PURCHASED", "AWAITING_PICKUP"];
export const LOGISTICS_STATUSES = [
  "AWAITING_PICKUP",
  "INLAND_TRANSPORT",
  "AT_ORIGIN_PORT",
  "IN_CONTAINER",
  "SEA_TRANSIT",
  "DESTINATION_PORT",
];
export const SHIPMENT_STATUS_RU: Record<string, string> = {
  PLANNED: "Запланирован",
  BOOKED: "Забронирован",
  AWAITING_PICKUP: "Ожидает забора",
  PICKED_UP: "Забран",
  IN_TRANSIT: "В пути",
  ARRIVED_AT_PORT: "Прибыл в порт",
  PORT_PROCESSING: "Обработка в порту",
  LOADED_IN_CONTAINER: "Загружен в контейнер",
  LOADED_ON_VESSEL: "Погружен на судно",
  SEA_TRANSIT: "В море",
  ARRIVED_DESTINATION_PORT: "Порт назначения",
  PORT_RELEASE: "Выпуск из порта",
  CUSTOMS_HANDOFF: "Передан на таможню",
  UA_INLAND_TRANSIT: "Доставка по Украине",
  DELIVERED: "Доставлен",
  DELAYED: "Задержка",
  ON_HOLD: "На паузе",
  CANCELLED: "Отменён",
};

export const SHIPMENT_TYPE_RU: Record<string, string> = {
  AUCTION_PICKUP: "Забор с аукциона",
  INLAND_TRUCK: "Наземная перевозка",
  RAIL: "Ж/Д перевозка",
  PORT_TRANSFER: "Доставка в порт",
  CONTAINER: "Контейнер",
  SEA_FREIGHT: "Морской фрахт",
  RO_RO: "Ro-Ro",
  EU_TRUCK: "Автовоз по Европе",
  UA_TRUCK: "Автовоз по Украине",
  TOW_TRUCK: "Эвакуатор",
  OTHER: "Другое",
};

export const DELAY_RU: Record<string, string> = {
  green: "В срок",
  yellow: "Небольшая задержка",
  orange: "Существенная задержка",
  red: "Критично / просрочено",
};

export const CASE_STATUS_RU: Record<string, string> = {
  AWAITING_ARRIVAL: "Ожидает прибытия",
  DOCUMENTS_PREP: "Сбор документов",
  SUBMITTED: "Подано брокеру / таможне",
  INSPECTION: "Осмотр",
  DUTY_CALCULATION: "Расчёт платежей",
  PAYMENT_PENDING: "К оплате",
  PAID: "Оплачено",
  CLEARED: "Выпущено / растаможено",
  CERTIFICATION: "Сертификация",
  REGISTRATION_PREP: "Подготовка к регистрации",
  REGISTERED: "Зарегистрировано",
  ON_HOLD: "На паузе",
  REJECTED: "Отказ",
};

export const CUSTOMS_STATUSES = ["CUSTOMS", "CUSTOMS_CLEARED"];
export const SALES_STATUSES = ["READY_FOR_SALE", "RESERVED", "SOLD"];

export function money(value: unknown, currency = "USD"): string {
  if (value == null || value === "") return "—";
  const n = Number(value);
  if (Number.isNaN(n)) return "—";
  return `${n.toLocaleString("ru-RU", { maximumFractionDigits: 2 })} ${currency}`;
}

export function vehicleTitle(row: Record<string, unknown>): string {
  const parts = [row.year, row.manufacturer, row.model].map((x) => String(x || "").trim()).filter(Boolean);
  return parts.join(" ") || String(row.vin || "Автомобиль");
}
