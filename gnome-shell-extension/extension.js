const St = imports.gi.St;
const Main = imports.ui.main;
const GLib = imports.gi.GLib;
const Mainloop = imports.mainloop;

const Me = imports.misc.extensionUtils.getCurrentExtension();
const Notification = Me.imports.notification;

const price_file = '/tmp/eos-price.csv';
const concerned_prices_file = '/tmp/eos-concerned-prices';

let price_label;
let stop = false;
let last_update_time = null;
// 价格超出此区间时发出提示
let concerned_prices = [50, 100];

function update_concerned_prices(){
  let content = get_file_content(concerned_prices_file);
  if (content) {
    let prices = content.trim().split('\n')[0].trim().split(' ');
    concerned_prices[0] = parseFloat(prices[0]);
    concerned_prices[1] = parseFloat(prices[1]);
  }
}

// 根据价格变化趋势或当前价格做出适当提示
function show_prompt(avg_prices, otcbtc_prices) {
  if (otcbtc_prices && otcbtc_prices.length) {
    let price = otcbtc_prices[otcbtc_prices.length - 1];
    if (price < concerned_prices[0]) {
      Notification.show('EOS 价格突破 ' + concerned_prices[0]);
      return;
    } else if (price > concerned_prices[1]) {
      Notification.show('EOS 价格突破 ' + concerned_prices[1]);
      return;
    }
  }

  // if (avg_prices && avg_prices.length >= 3) {
  //   avg_prices.reverse();
  //   if (avg_prices[0] > avg_prices[1] && avg_prices[1] > avg_prices[2] && avg_prices[0] - avg_prices[2] > 0.3) {
  //     Notification.show('EOS 涨价中');
  //   } else if (avg_prices[0] < avg_prices[1] && avg_prices[1] < avg_prices[2] && avg_prices[2] - avg_prices[0] > 0.3) {
  //     Notification.show('EOS 降价中');
  //   }
  // }
}

function prices_to_text(prices) {
  let start = prices.length > 5 ? prices.length - 5 : 0;
  let text = prices[start] + '';
  for (let i = start + 1; i < prices.length; i++) {
    if (prices[i] > prices[i-1]) {
      text += '↗' + prices[i];
    } else if (prices[i] == prices[i-1]) {
      text += '→' + prices[i];
    } else {
      text += '↘' + prices[i];
    }
  }
  return text;
}

function get_file_content(filename) {
  try {
    let [ok, content] = GLib.file_get_contents(filename);
    if (ok){
      return content.toString();
    } else {
      return null;
    }
  } catch (e) {
    return null;
  }
}

function load_prices() {
  let content = get_file_content(price_file);
  if (!content){
    return;
  }

  let lines = content.toString().trim().split("\n");
  lines = lines.slice(Math.max(lines.length - 20 - 1, 1));
  if (lines.length < 1) {
    return;
  }

  let update_time = lines[lines.length - 1].split(',')[0];
  if (update_time == last_update_time) {
    return;
  }

  last_update_time = update_time;

  let avg_prices = [];
  let otcbtc_prices = [];
  for (let i = 0; i < lines.length; i++) {
    let parts = lines[i].split(',');
    let avg_price = parseFloat(parts[3]) || null;
    let otcbtc_price = parseFloat(parts[4]) || null;
    if (avg_price) {
      avg_prices.push(avg_price);
    }
    if (otcbtc_price) {
      otcbtc_prices.push(otcbtc_price);
    }
  }

  if (avg_prices.length && otcbtc_prices.length) {
    price_label.set_text('EOS: ' + prices_to_text(avg_prices) +
                         '\tOTCBTC: ' + prices_to_text(otcbtc_prices));

    show_prompt(avg_prices, otcbtc_prices);
  }
}


function init() {
  price_label = new St.Label();
  price_label.set_text('EOS Price');
  price_label.set_style_class_name('eos-price');
  price_label.clutter_text.set_x_align(3); // 右对齐
  price_label.set_width(600);
  price_label.set_position(
    Main.panel._centerBox.get_allocation_box().get_x() - price_label.get_width() - 10,
    3
  );
}

function enable() {
  Main.uiGroup.add_actor(price_label);

  stop = false;
  last_update_time = null;
  load_prices();
  update_concerned_prices();

  Mainloop.timeout_add(10000, function() {
    load_prices();
    return !stop;
  });

  Mainloop.timeout_add(60000, function() {
    update_concerned_prices();
    return !stop;
  });
}

function disable() {
  Main.uiGroup.remove_actor(price_label);
  stop = true;
}
