from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Fix column name from curriculum_id_id to curriculum_id in core_taskmanage table'

    def handle(self, *args, **options):
        self.stdout.write("컬럼명 변경을 시작합니다...")
        
        try:
            with connection.cursor() as cursor:
                # 먼저 현재 테이블이 존재하는지 확인
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'core_taskmanage'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    self.stdout.write(self.style.ERROR("core_taskmanage 테이블이 존재하지 않습니다."))
                    return
                    
                self.stdout.write(self.style.SUCCESS("core_taskmanage 테이블을 찾았습니다."))
                
                # 현재 테이블의 curriculum 관련 컬럼 확인
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = 'core_taskmanage' 
                    AND column_name LIKE '%curriculum%';
                """)
                curriculum_columns = cursor.fetchall()
                self.stdout.write("curriculum 관련 컬럼들:")
                for col in curriculum_columns:
                    self.stdout.write(f"  - {col[0]} ({col[1]})")
                
                # curriculum_id_id 컬럼이 존재하는지 확인
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'core_taskmanage' 
                    AND column_name = 'curriculum_id_id';
                """)
                old_column = cursor.fetchone()
                
                # curriculum_id 컬럼이 이미 존재하는지 확인
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'core_taskmanage' 
                    AND column_name = 'curriculum_id';
                """)
                new_column = cursor.fetchone()
                
                if old_column and new_column:
                    self.stdout.write(self.style.WARNING("curriculum_id_id와 curriculum_id 컬럼이 둘 다 존재합니다!"))
                    
                elif old_column:
                    self.stdout.write(self.style.SUCCESS("curriculum_id_id 컬럼을 찾았습니다. 변경을 시작합니다..."))
                    
                    # 컬럼명 변경
                    cursor.execute("ALTER TABLE core_taskmanage RENAME COLUMN curriculum_id_id TO curriculum_id;")
                    
                    # 변경 결과 확인
                    cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'core_taskmanage' 
                        AND column_name = 'curriculum_id';
                    """)
                    verify_result = cursor.fetchone()
                    
                    if verify_result:
                        self.stdout.write(self.style.SUCCESS("✅ 컬럼명이 성공적으로 변경되었습니다!"))
                    else:
                        self.stdout.write(self.style.ERROR("컬럼명 변경 확인 실패"))
                        
                elif new_column:
                    self.stdout.write(self.style.SUCCESS("curriculum_id 컬럼이 이미 존재합니다."))
                    self.stdout.write("컬럼명이 이미 올바르게 설정되어 있습니다.")
                    
                else:
                    self.stdout.write(self.style.ERROR("curriculum_id_id와 curriculum_id 컬럼 둘 다 찾을 수 없습니다."))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"전체 작업 실패: {e}"))
            import traceback
            traceback.print_exc()
