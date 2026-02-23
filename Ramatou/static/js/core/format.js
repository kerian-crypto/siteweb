export function formatMoney(value) {
  return `${new Intl.NumberFormat("fr-FR").format(value)} FCFA`;
}
