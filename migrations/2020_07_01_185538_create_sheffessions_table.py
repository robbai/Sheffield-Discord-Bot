from orator.migrations import Migration


class CreateSheffessionsTable(Migration):

    def up(self):
        """
        Run the migrations.
        """
        with self.schema.create('sheffessions') as table:
            table.integer('id').primary()
            table.long_text('post_text').nullable()
            table.string('post_url').nullable()
            table.datetime('post_date')
            table.string('image_url', 511).nullable()
            table.string('video_url', 511).nullable()

    def down(self):
        """
        Revert the migrations.
        """
        self.schema.drop('sheffessions')
