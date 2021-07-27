from datetime import datetime, timedelta
from time import sleep

from lectarium_app import app, scheduler


@app.shell_context_processor
def make_shell_context():
    import lectarium_app
    import lectarium_app.models as models
    context = vars(lectarium_app)
    context.update(vars(models))
    context["datetime"] = datetime
    context["timedelta"] = timedelta
    context["sleep"] = sleep
    return context


if app.config['ENABLE_SCHEDULER']:
    scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=app.config['ENABLE_RELOAD'])
