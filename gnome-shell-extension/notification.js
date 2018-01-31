const St = imports.gi.St;
const Main = imports.ui.main;
const Tweener = imports.ui.tweener;

let label;

function hide() {
  if (label) {
    Main.uiGroup.remove_actor(label);
    label.destroy();
  }
}

function show(text) {
  if (label) {
    // 取消未完成的动画
    Tweener.removeTweens(label);
    label.destroy();
  }

  label = new St.Label();
  label.set_style_class_name('notification');
  label.set_opacity(255);
  label.set_text(text);

  Main.uiGroup.add_actor(label);

  Tweener.addTween(label, {
    opacity: 0,
    time: 3,
    transition: 'easeInExpo',
    onStart: function() {
      let monitor = Main.layoutManager.primaryMonitor;
      // 开始之前无法获取到准确的 label.width
      label.set_position(monitor.x + Math.floor((monitor.width - label.width) / 2),
                          25);
      },
    onComplete: hide,
  });
}